import hashlib
import json
import logging
import queue
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from extensions import db
from orchestration.ai.factory import create_ai_provider
from orchestration.ai.prompts import PROMPT_VERSION, SYSTEM_PROMPT, build_incident_prompt
from orchestration.interfaces.ai_interface import AIAnalysisService
from orchestration.models.event_store import AIAnalysisStore, AIAnalysisCache
from utils.time import to_iso
from orchestration.models.incident import OrchestrationIncident

logger = logging.getLogger(__name__)


class AIAnalysisQueue:
    """Thread-safe singleton queue with configurable max concurrency."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, max_concurrent=None):
        self._shutdown = False
        if getattr(self, '_initialized', False):
            return
        self._queue = queue.Queue()
        self._active_count = 0
        self._active_lock = threading.Lock()
        self._max_concurrent_override = max_concurrent
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        self._initialized = True
        logger.info("AI queue initialized (thread started: %s)", self._worker_thread.is_alive())

    @property
    def max_concurrent(self):
        if self._max_concurrent_override is not None:
            return self._max_concurrent_override
        from flask import current_app
        try:
            return int(current_app.config.get("AI_MAX_CONCURRENT_REQUESTS", 3))
        except Exception:
            return 3

    @property
    def use_cache(self):
        from flask import current_app
        try:
            val = current_app.config.get("AI_ANALYSIS_CACHE", "true")
            return str(val).lower() == "true"
        except Exception:
            return True

    @property
    def use_backoff(self):
        from flask import current_app
        try:
            val = current_app.config.get("AI_RATE_LIMIT_BACKOFF", "true")
            return str(val).lower() == "true"
        except Exception:
            return True

    def enqueue(self, incident_id: str, app):
        self._queue.put((incident_id, app))
        logger.info("AI queued: incident %s (queue size: %d)", incident_id, self._queue.qsize())

    def _worker_loop(self):
        logger.info("AI queue worker loop started")
        while not self._shutdown:
            try:
                with self._active_lock:
                    if self._active_count >= self.max_concurrent:
                        time.sleep(0.5)
                        continue

                incident_id, app = self._queue.get(timeout=1)

                with self._active_lock:
                    self._active_count += 1

                logger.info("AI processing started: incident %s (active: %d/%d, app=%s)", incident_id, self._active_count, self.max_concurrent, bool(app))
                thread = threading.Thread(
                    target=self._run_with_cleanup,
                    args=(incident_id, app),
                    daemon=True,
                )
                thread.start()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error("AI queue worker error: %s", e, exc_info=True)
                time.sleep(1)

    def _log_active_count(self):
        logger.info("AI queue active count: %d/%d", self._active_count, self.max_concurrent)

    def _run_with_cleanup(self, incident_id: str, app):
        try:
            run_async_analysis(incident_id, app)
        finally:
            with self._active_lock:
                self._active_count = max(0, self._active_count - 1)
                self._log_active_count()
            logger.info("AI processing completed: incident %s (active: %d/%d)", incident_id, self._active_count, self.max_concurrent)

    def shutdown(self):
        self._shutdown = True


def _build_incident_signature(incident: OrchestrationIncident) -> str:
    """Build a deterministic signature for an incident to detect duplicates."""
    raw = f"{incident.repository}|{incident.branch}|{incident.build_number}|{incident.category}|{incident.severity}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _find_recent_similar_analysis(incident: OrchestrationIncident) -> Optional[AIAnalysisStore]:
    """Check if a similar incident was analyzed within the last 5 minutes."""
    try:
        five_min_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
        signature = _build_incident_signature(incident)
        cache_entry = AIAnalysisCache.query.filter(
            AIAnalysisCache.incident_signature == signature,
            AIAnalysisCache.created_at >= five_min_ago,
        ).order_by(AIAnalysisCache.created_at.desc()).first()
        if cache_entry:
            analysis = AIAnalysisStore.query.get(cache_entry.analysis_id)
            if analysis:
                logger.info("AI cache HIT for incident %s (signature: %s, reusing analysis #%d)", incident.incident_id, signature[:12], analysis.id)
                return analysis
    except Exception as e:
        logger.warning("AI cache lookup failed: %s", e)
    return None


def _store_in_cache(incident: OrchestrationIncident, analysis_id: int):
    """Store the analysis result in the cache for future dedup."""
    try:
        signature = _build_incident_signature(incident)
        existing = AIAnalysisCache.query.filter_by(incident_signature=signature).first()
        if existing:
            existing.analysis_id = analysis_id
            existing.created_at = datetime.now(timezone.utc)
        else:
            entry = AIAnalysisCache(
                incident_signature=signature,
                analysis_id=analysis_id,
                incident_id=incident.incident_id,
                source=incident.category,
                event_type=incident.category,
                affected_component=incident.repository,
            )
            db.session.add(entry)
        db.session.commit()
        logger.info("AI cache stored for incident %s (signature: %s)", incident.incident_id, signature[:12])
    except Exception as e:
        db.session.rollback()
        logger.warning("AI cache store failed: %s", e)


class AIService(AIAnalysisService):
    def __init__(self):
        self._provider = None

    def _get_provider(self):
        if self._provider is None:
            self._provider = create_ai_provider()
        return self._provider

    def analyze_incident(self, incident: OrchestrationIncident, evidence: List[Any]) -> Dict[str, Any]:
        provider = self._get_provider()
        if not provider:
            return {"error": "No AI provider configured"}

        incident_dict = incident.to_dict() if hasattr(incident, "to_dict") else {"id": getattr(incident, "incident_id", ""), "summary": getattr(incident, "summary", str(incident))}

        evidence_list = []
        for e in (evidence or incident.evidence or []):
            evidence_list.append(e.to_dict() if hasattr(e, "to_dict") else {"type": str(type(e).__name__), "content": str(e)})

        timeline_list = []
        for t in (incident.timeline or []):
            timeline_list.append(t.to_dict() if hasattr(t, "to_dict") else {"timestamp": str(t)})

        related = self._get_related_incidents(incident)
        related_list = [{"summary": r.summary, "status": r.status} for r in related]

        prompt = build_incident_prompt(incident_dict, evidence_list, timeline_list, related_list)
        result = provider.analyze(prompt, system_prompt=SYSTEM_PROMPT)
        return result or {"error": "AI provider returned no result"}

    def summarize_logs(self, logs: List[str]) -> str:
        provider = self._get_provider()
        if not provider:
            return "AI provider not configured"

        blob = "\n".join(logs[:500])
        prompt = f"Summarise the following log entries in 2-3 sentences. Focus on errors, warnings, and anomalies:\n\n{blob}"
        result = provider.analyze(prompt, system_prompt="You are a log analysis assistant. Respond ONLY with a JSON object with a 'summary' field.")
        if result and "summary" in result:
            return result["summary"]
        return "AI analysis unavailable"

    def suggest_fixes(self, incident: OrchestrationIncident, context: Dict[str, Any]) -> List[str]:
        ev = context.get("evidence", []) if isinstance(context, dict) else []
        result = self.analyze_incident(incident, ev)
        if isinstance(result, dict) and "suggested_fixes" in result:
            return result["suggested_fixes"]
        return ["Unable to generate suggestions"]

    def estimate_confidence(self, incident: OrchestrationIncident, analysis: Dict[str, Any]) -> float:
        return float(analysis.get("confidence", 0.5))

    def classify_root_cause(self, incident: OrchestrationIncident, evidence: List[Any]) -> str:
        result = self.analyze_incident(incident, evidence)
        if isinstance(result, dict):
            return result.get("root_cause", "unknown")
        return "unknown"

    def _get_related_incidents(self, incident: OrchestrationIncident) -> List[OrchestrationIncident]:
        try:
            from orchestration.services.orchestration_service import get_orchestrator
            svc = get_orchestrator()
            recent = svc.get_all_incidents()
            return [i for i in recent if i.incident_id != incident.incident_id and i.repository == incident.repository][:5]
        except Exception:
            return []


def _store_analysis_to_db(incident_id: str, result: Dict[str, Any], provider_name: str, model_name: str, project_id: int = None):
    try:
        record = AIAnalysisStore(
            project_id=project_id,
            incident_id=incident_id,
            summary=result.get("summary", ""),
            root_cause=result.get("root_cause", ""),
            confidence=float(result.get("confidence", 0.0)),
            severity=result.get("severity", ""),
            affected_components_json=json.dumps(result.get("affected_components", [])),
            possible_causes_json=json.dumps(result.get("possible_causes", [])),
            suggested_fixes_json=json.dumps(result.get("suggested_fixes", [])),
            preventive_actions_json=json.dumps(result.get("preventive_actions", [])),
            similar_patterns_json=json.dumps(result.get("similar_patterns", [])),
            risk_assessment=result.get("risk_assessment", ""),
            estimated_resolution_time=result.get("estimated_resolution_time", ""),
            requires_human=bool(result.get("requires_human", False)),
            provider=provider_name,
            model=model_name,
            prompt_version=PROMPT_VERSION,
            analyzed_at=datetime.now(timezone.utc),
        )
        db.session.add(record)
        db.session.commit()
        logger.info("AI analysis saved to DB for incident %s", incident_id)
        return record.id
    except Exception as e:
        db.session.rollback()
        logger.error("Failed to save AI analysis to DB: %s", e)
        return None


def _store_rate_limited_status(incident_id: str):
    """Store a rate-limited placeholder so the incident has a record."""
    try:
        record = AIAnalysisStore(
            incident_id=incident_id,
            summary="Analysis rate-limited by AI provider",
            root_cause="pending",
            confidence=0.0,
            severity="",
            provider="rate_limited",
            model="",
            prompt_version=PROMPT_VERSION,
            analyzed_at=datetime.now(timezone.utc),
        )
        db.session.add(record)
        db.session.commit()
        logger.info("AI rate-limited status stored for incident %s", incident_id)
    except Exception as e:
        db.session.rollback()
        logger.warning("Failed to store rate-limited status: %s", e)


def run_async_analysis(incident_id: str, app=None):
    ctx = app.app_context() if app else None
    if ctx:
        ctx.push()
    try:
        from orchestration.services.orchestration_service import get_orchestrator

        logger.info("=== AI: looking up incident %s ===", incident_id)

        svc = get_orchestrator()

        incident = svc.get_incident(incident_id)
        if not incident:
            logger.warning("Incident %s not found for AI analysis (incident_store size=%d)", incident_id, len(svc.incident_service._incidents))
            return

        logger.info("=== AI: found incident %s (%s) ===", incident_id, incident.summary)

        # Dedup: check if a similar incident was recently analyzed
        queue_svc = AIAnalysisQueue()
        if queue_svc.use_cache:
            cached = _find_recent_similar_analysis(incident)
            if cached:
                logger.info("AI dedup HIT for incident %s — reusing analysis #%d from incident %s", incident_id, cached.id, cached.incident_id)
                now = datetime.now(timezone.utc)
                incident.ai_analysis = cached.summary
                incident.root_cause = cached.root_cause
                incident.confidence_score = cached.confidence
                import json
                incident.suggested_fixes = json.loads(cached.suggested_fixes_json) if cached.suggested_fixes_json else []
                incident.possible_causes = json.loads(cached.possible_causes_json) if cached.possible_causes_json else []
                incident.preventive_actions = json.loads(cached.preventive_actions_json) if cached.preventive_actions_json else []
                incident.risk_assessment = cached.risk_assessment
                incident.estimated_resolution_time = cached.estimated_resolution_time
                incident.requires_human = cached.requires_human
                incident.affected_components = json.loads(cached.affected_components_json) if cached.affected_components_json else []
                incident.ai_metadata = {
                    "cached": True,
                    "source_incident": cached.incident_id,
                    "provider": cached.provider,
                    "model": cached.model,
                    "analyzed_at": to_iso(cached.analyzed_at) or to_iso(now),
                    "prompt_version": PROMPT_VERSION,
                }
                svc.incident_service.add_timeline_event(
                    incident_id,
                    "ai_analysis_reused",
                    "ai_service",
                    f"AI analysis reused from incident {cached.incident_id} (confidence: {cached.confidence:.0%})",
                    {"cached": True, "source_incident": cached.incident_id, "confidence": cached.confidence},
                )
                _store_in_cache(incident, cached.id)
                logger.info("AI dedup complete for incident %s", incident_id)
                return

        ai = AIService()
        result = ai.analyze_incident(incident, incident.evidence or [])

        if result and "error" not in result:
            provider = ai._get_provider()
            provider_name = provider.name() if provider else "unknown"
            model_name = provider.model_name() if provider else "unknown"
            now = datetime.now(timezone.utc)

            incident.ai_analysis = result.get("summary", "")
            incident.root_cause = result.get("root_cause", "")
            incident.confidence_score = float(result.get("confidence", 0.0))
            incident.suggested_fixes = result.get("suggested_fixes", [])
            incident.possible_causes = result.get("possible_causes", [])
            incident.preventive_actions = result.get("preventive_actions", [])
            incident.similar_patterns = result.get("similar_patterns", [])
            incident.risk_assessment = result.get("risk_assessment", "")
            incident.estimated_resolution_time = result.get("estimated_resolution_time", "")
            incident.requires_human = bool(result.get("requires_human", False))
            incident.affected_components = result.get("affected_components", [])
            incident.severity = result.get("severity", incident.severity)
            incident.prompt_version = PROMPT_VERSION
            incident.ai_metadata = {
                "provider": provider_name,
                "model": model_name,
                "analyzed_at": to_iso(now),
                "severity": result.get("severity"),
                "affected_components": result.get("affected_components", []),
                "similar_patterns": result.get("similar_patterns", []),
                "risk_assessment": result.get("risk_assessment", ""),
                "estimated_resolution_time": result.get("estimated_resolution_time", ""),
                "requires_human": bool(result.get("requires_human", False)),
                "prompt_version": PROMPT_VERSION,
            }

            svc.incident_service.add_timeline_event(
                incident_id,
                "ai_analysis_completed",
                "ai_service",
                f"AI analysis completed (confidence: {incident.confidence_score:.0%}, root cause: {incident.root_cause})",
                {"provider": provider_name, "model": model_name, "confidence": incident.confidence_score},
            )

            analysis_id = _store_analysis_to_db(
                incident_id, result, provider_name, model_name,
                project_id=getattr(incident, "project_id", None),
            )
            if analysis_id and queue_svc.use_cache:
                _store_in_cache(incident, analysis_id)

            logger.info("AI analysis complete for incident %s", incident_id)
        else:
            error_detail = str(result) if result else "AI provider returned no result"
            is_rate_limited = "429" in error_detail or "Too Many Requests" in error_detail or "rate_limit" in error_detail.lower()

            if is_rate_limited and queue_svc.use_backoff:
                logger.warning("AI rate-limited for incident %s — storing status", incident_id)
                _store_rate_limited_status(incident_id)
                svc.incident_service.add_timeline_event(
                    incident_id,
                    "ai_analysis_rate_limited",
                    "ai_service",
                    "AI analysis rate-limited by provider — will retry",
                    {"status": "rate_limited"},
                )
            else:
                logger.warning("AI analysis returned no useful result for incident %s: %s", incident_id, result)
                svc.incident_service.add_timeline_event(
                    incident_id,
                    "ai_analysis_failed",
                    "ai_service",
                    "AI analysis completed but returned no useful result",
                )
    except Exception as e:
        logger.error("AI analysis failed for incident %s: %s", incident_id, e, exc_info=True)
        try:
            from orchestration.services.orchestration_service import get_orchestrator
            svc = get_orchestrator()
            svc.incident_service.add_timeline_event(
                incident_id,
                "ai_analysis_error",
                "ai_service",
                f"AI analysis failed: {str(e)[:200]}",
            )
        except Exception:
            pass
    finally:
        if ctx:
            ctx.pop()


def trigger_ai_analysis(incident_id: str):
    try:
        from flask import current_app
        app = current_app._get_current_object()
        logger.info("AI trigger: got Flask app for incident %s", incident_id)
    except (RuntimeError, AssertionError) as e:
        app = None
        logger.warning("AI trigger: no Flask app context for incident %s: %s", incident_id, e)

    queue_svc = AIAnalysisQueue()
    queue_svc.enqueue(incident_id, app)
    logger.info("AI trigger: enqueued incident %s (queue size approx %d)", incident_id, queue_svc._queue.qsize())
