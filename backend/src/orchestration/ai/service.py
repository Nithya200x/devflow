import json
import logging
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from extensions import db
from orchestration.ai.factory import create_ai_provider
from orchestration.ai.prompts import PROMPT_VERSION, SYSTEM_PROMPT, build_incident_prompt
from orchestration.interfaces.ai_interface import AIAnalysisService
from orchestration.models.event_store import AIAnalysisStore
from orchestration.models.incident import OrchestrationIncident

logger = logging.getLogger(__name__)


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


def _store_analysis_to_db(incident_id: str, result: Dict[str, Any], provider_name: str, model_name: str):
    try:
        record = AIAnalysisStore(
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
            analyzed_at=datetime.utcnow(),
        )
        db.session.add(record)
        db.session.commit()
        logger.info("AI analysis saved to DB for incident %s", incident_id)
    except Exception as e:
        db.session.rollback()
        logger.error("Failed to save AI analysis to DB: %s", e)


def run_async_analysis(incident_id: str, app=None):
    ctx = app.app_context() if app else None
    if ctx:
        ctx.push()
    try:
        from orchestration.services.orchestration_service import get_orchestrator

        logger.info("=== AI: looking up incident %s ===", incident_id)

        svc = get_orchestrator()

        logger.info("=== AI: incident lookup with shared OrchestrationService singleton ===")

        incident = svc.get_incident(incident_id)
        if not incident:
            logger.warning("Incident %s not found for AI analysis (incident_store size=%d)", incident_id, len(svc.incident_service._incidents))
            return

        logger.info("=== AI: found incident %s (%s) ===", incident_id, incident.summary)

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
                "analyzed_at": now.isoformat(),
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

            _store_analysis_to_db(incident_id, result, provider_name, model_name)

            logger.info("AI analysis complete for incident %s", incident_id)
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
    except (RuntimeError, AssertionError):
        app = None
    thread = threading.Thread(target=run_async_analysis, args=(incident_id, app), daemon=True)
    thread.start()
    logger.info("Triggered async AI analysis for incident %s", incident_id)
