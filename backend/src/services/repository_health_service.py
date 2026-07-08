import datetime
import logging
import threading
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class RepositoryHealthService:
    WEIGHTS = {
        "github": 20,
        "cicd": 20,
        "deployment": 15,
        "infrastructure": 15,
        "monitoring": 10,
        "activity": 10,
        "incidents": 10,
    }

    def __init__(self):
        self._cache: Dict[int, Dict[str, Any]] = {}
        self._cache_lock = threading.Lock()
        self._cache_ttl = 45

    def _get_cached(self, project_id: int) -> Optional[Dict[str, Any]]:
        entry = self._cache.get(project_id)
        if entry:
            age = (datetime.datetime.now(datetime.timezone.utc) - entry["calculated_at"]).total_seconds()
            if age < self._cache_ttl:
                return entry
        return None

    def _set_cache(self, project_id: int, result: Dict[str, Any]):
        self._cache[project_id] = {**result, "calculated_at": datetime.datetime.now(datetime.timezone.utc)}

    def invalidate(self, project_id: Optional[int] = None):
        with self._cache_lock:
            if project_id is not None:
                self._cache.pop(project_id, None)
            else:
                self._cache.clear()

    def _get_previous_score(self, project_id: int) -> Optional[int]:
        prev = self._cache.get(project_id)
        if prev:
            return prev.get("score")
        return None

    def calculate_score(self, project_id: int, overview: Dict[str, Any]) -> Dict[str, Any]:
        cached = self._get_cached(project_id)
        if cached:
            return cached

        breakdown = {}
        details = {}

        github_score = self._score_github(overview)
        breakdown["github"] = github_score
        details["github"] = self._explain_github(overview)

        cicd_score = self._score_cicd(overview)
        breakdown["cicd"] = cicd_score
        details["cicd"] = self._explain_cicd(overview)

        deployment_score = self._score_deployment(overview)
        breakdown["deployment"] = deployment_score
        details["deployment"] = self._explain_deployment(overview)

        infrastructure_score = self._score_infrastructure(overview)
        breakdown["infrastructure"] = infrastructure_score
        details["infrastructure"] = self._explain_infrastructure(overview)

        monitoring_score = self._score_monitoring(overview)
        breakdown["monitoring"] = monitoring_score
        details["monitoring"] = self._explain_monitoring(overview)

        activity_score = self._score_activity(overview)
        breakdown["activity"] = activity_score
        details["activity"] = self._explain_activity(overview)

        incidents_score = self._score_incidents(overview)
        breakdown["incidents"] = incidents_score
        details["incidents"] = self._explain_incidents(overview)

        score = sum(
            min(breakdown.get(k, 0), self.WEIGHTS[k])
            for k in self.WEIGHTS
        )
        score = max(0, min(100, score))
        max_possible = sum(self.WEIGHTS.values())

        previous_score = self._get_previous_score(project_id)
        if previous_score is not None:
            diff = score - previous_score
            if diff > 2:
                trend = "improving"
            elif diff < -2:
                trend = "degrading"
            else:
                trend = "stable"
        else:
            trend = "stable"

        colors = self._score_color(score)

        result = {
            "score": score,
            "max_score": max_possible,
            "breakdown": breakdown,
            "weights": self.WEIGHTS,
            "details": details,
            "trend": trend,
            "color": colors["hex"],
            "css_color": colors["css"],
            "label": colors["label"],
            "calculated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        with self._cache_lock:
            self._set_cache(project_id, result)

        return result

    @staticmethod
    def _score_color(score: int) -> Dict[str, str]:
        if score >= 95:
            return {"hex": "#10b981", "css": "var(--success-color)", "label": "Excellent"}
        elif score >= 80:
            return {"hex": "#22c55e", "css": "var(--success-color)", "label": "Healthy"}
        elif score >= 65:
            return {"hex": "#3b82f6", "css": "var(--info-color)", "label": "Stable"}
        elif score >= 50:
            return {"hex": "#f59e0b", "css": "var(--warning-color)", "label": "Needs Attention"}
        else:
            return {"hex": "#ef4444", "css": "var(--danger-color)", "label": "Critical"}

    @staticmethod
    def _score_github(overview: Dict[str, Any]) -> int:
        gh = overview.get("github", {})
        score = 0
        if gh.get("connected"):
            score += 5
        if gh.get("service_status") == "connected":
            score += 4
        if gh.get("default_branch"):
            score += 3
        if gh.get("latest_commit_sha"):
            score += 3
        if gh.get("latest_commit_date"):
            score += 3
        if gh.get("branch_count", 0) > 0:
            score += 2
        return min(score, 20)

    @staticmethod
    def _explain_github(overview: Dict[str, Any]) -> Dict[str, Any]:
        gh = overview.get("github", {})
        return {
            "connected": bool(gh.get("connected")),
            "api_reachable": gh.get("service_status") == "connected",
            "default_branch": bool(gh.get("default_branch")),
            "latest_commit": bool(gh.get("latest_commit_sha")),
            "branches": gh.get("branch_count", 0),
            "max_score": 20,
            "earned": RepositoryHealthService._score_github(overview),
        }

    @staticmethod
    def _score_cicd(overview: Dict[str, Any]) -> int:
        cicd = overview.get("cicd", {})
        gh = overview.get("github", {})
        score = 0
        workflows = cicd.get("workflows", [])
        runs = cicd.get("recent_runs", [])
        if workflows:
            score += 4
        success_runs = [r for r in runs if r.get("conclusion") == "success"]
        total_runs = len(runs)
        if total_runs > 0:
            rate = len(success_runs) / total_runs
            score += int(rate * 8)
        if cicd.get("has_deploy_workflow"):
            score += 4
        failed = cicd.get("failed_workflows", 0)
        score -= min(failed * 2, 6)
        return max(0, min(score, 20))

    @staticmethod
    def _explain_cicd(overview: Dict[str, Any]) -> Dict[str, Any]:
        cicd = overview.get("cicd", {})
        runs = cicd.get("recent_runs", [])
        success = len([r for r in runs if r.get("conclusion") == "success"])
        return {
            "workflows_configured": len(cicd.get("workflows", [])),
            "recent_runs": len(runs),
            "successful_runs": success,
            "has_deploy_workflow": cicd.get("has_deploy_workflow", False),
            "failed_workflows": cicd.get("failed_workflows", 0),
            "max_score": 20,
            "earned": RepositoryHealthService._score_cicd(overview),
        }

    @staticmethod
    def _score_deployment(overview: Dict[str, Any]) -> int:
        dep = overview.get("deployment", {})
        score = 0
        if dep.get("last_deployment_successful"):
            score += 5
        if dep.get("rollback_status") in (None, "none", "successful"):
            score += 3
        freq = dep.get("deployment_frequency", 0)
        if freq >= 10:
            score += 4
        elif freq >= 5:
            score += 3
        elif freq >= 1:
            score += 2
        envs = dep.get("environments", [])
        if len(envs) >= 2:
            score += 3
        elif len(envs) >= 1:
            score += 2
        return min(score, 15)

    @staticmethod
    def _explain_deployment(overview: Dict[str, Any]) -> Dict[str, Any]:
        dep = overview.get("deployment", {})
        return {
            "last_successful": dep.get("last_deployment_successful", False),
            "rollback_status": dep.get("rollback_status", "none"),
            "frequency_7d": dep.get("deployment_frequency", 0),
            "environments": dep.get("environments", []),
            "max_score": 15,
            "earned": RepositoryHealthService._score_deployment(overview),
        }

    @staticmethod
    def _score_infrastructure(overview: Dict[str, Any]) -> int:
        score = 0
        docker = overview.get("docker", {})
        k8s = overview.get("kubernetes", {})
        prom = overview.get("prometheus", {})
        graf = overview.get("grafana", {})
        am = overview.get("alertmanager", {})

        if docker.get("service_status") == "connected":
            score += 3
            if docker.get("running"):
                score += 1
        if k8s.get("service_status") == "connected":
            score += 3
            k8s_ready = k8s.get("ready_pods", 0)
            k8s_total = k8s.get("total_pods", 0)
            if k8s_total > 0 and k8s_ready == k8s_total:
                score += 1
        if prom.get("service_status") == "connected" and prom.get("healthy"):
            score += 3
        if graf.get("service_status") == "connected" and graf.get("dashboard_uid"):
            score += 2
        if am.get("service_status") == "connected":
            score += 2
        return min(score, 15)

    @staticmethod
    def _explain_infrastructure(overview: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "docker": overview.get("docker", {}).get("service_status", "not_configured"),
            "kubernetes": overview.get("kubernetes", {}).get("service_status", "not_configured"),
            "prometheus": overview.get("prometheus", {}).get("service_status", "not_configured"),
            "grafana": overview.get("grafana", {}).get("service_status", "not_configured"),
            "alertmanager": overview.get("alertmanager", {}).get("service_status", "not_configured"),
            "max_score": 15,
            "earned": RepositoryHealthService._score_infrastructure(overview),
        }

    @staticmethod
    def _score_monitoring(overview: Dict[str, Any]) -> int:
        prom = overview.get("prometheus", {})
        am = overview.get("alertmanager", {})
        score = 6
        active_alerts = prom.get("active_alerts", 0) or am.get("active_alerts", 0)
        critical_alerts = prom.get("critical_alerts", 0) or am.get("critical_alerts", 0)
        score -= min(active_alerts, 4)
        score -= min(critical_alerts * 2, 4)
        return max(0, min(score, 10))

    @staticmethod
    def _explain_monitoring(overview: Dict[str, Any]) -> Dict[str, Any]:
        prom = overview.get("prometheus", {})
        am = overview.get("alertmanager", {})
        return {
            "active_alerts": prom.get("active_alerts", 0) or am.get("active_alerts", 0),
            "critical_alerts": prom.get("critical_alerts", 0) or am.get("critical_alerts", 0),
            "prometheus_healthy": prom.get("healthy", False),
            "max_score": 10,
            "earned": RepositoryHealthService._score_monitoring(overview),
        }

    @staticmethod
    def _score_activity(overview: Dict[str, Any]) -> int:
        gh = overview.get("github", {})
        score = 0
        if gh.get("latest_commit_date"):
            try:
                dt = datetime.datetime.fromisoformat(gh["latest_commit_date"].replace("Z", "+00:00"))
                days_ago = (datetime.datetime.now(datetime.timezone.utc) - dt).days
                if days_ago <= 1:
                    score += 4
                elif days_ago <= 7:
                    score += 3
                elif days_ago <= 30:
                    score += 2
                else:
                    score += 1
            except Exception:
                score += 1
        open_prs = gh.get("open_prs", 0)
        if open_prs > 0:
            score += 2
        total_prs = gh.get("total_prs", 0)
        if total_prs > 0:
            merged_ratio = (total_prs - open_prs) / total_prs if total_prs > 0 else 0
            if merged_ratio > 0.5:
                score += 2
        branch_count = gh.get("branch_count", 0)
        if branch_count >= 2:
            score += 2
        return min(score, 10)

    @staticmethod
    def _explain_activity(overview: Dict[str, Any]) -> Dict[str, Any]:
        gh = overview.get("github", {})
        return {
            "latest_commit": gh.get("latest_commit_date", ""),
            "open_prs": gh.get("open_prs", 0),
            "total_prs": gh.get("total_prs", 0),
            "branches": gh.get("branch_count", 0),
            "max_score": 10,
            "earned": RepositoryHealthService._score_activity(overview),
        }

    @staticmethod
    def _score_incidents(overview: Dict[str, Any]) -> int:
        inc = overview.get("incidents", {})
        score = 6
        open_incidents = inc.get("open_count", 0)
        score -= min(open_incidents * 2, 4)
        if inc.get("has_rca"):
            score += 2
        resolution_rate = inc.get("resolution_rate", 1.0)
        score = int(score * resolution_rate)
        mttr = inc.get("mean_resolution_minutes", 0)
        if mttr > 0 and mttr < 60:
            score += 1
        return max(0, min(score, 10))

    @staticmethod
    def _explain_incidents(overview: Dict[str, Any]) -> Dict[str, Any]:
        inc = overview.get("incidents", {})
        return {
            "open_incidents": inc.get("open_count", 0),
            "total_incidents": inc.get("total_count", 0),
            "has_rca": inc.get("has_rca", False),
            "resolution_rate": inc.get("resolution_rate", 1.0),
            "mean_resolution_minutes": inc.get("mean_resolution_minutes", 0),
            "max_score": 10,
            "earned": RepositoryHealthService._score_incidents(overview),
        }


_singleton = None


def get_health_service():
    global _singleton
    if _singleton is None:
        _singleton = RepositoryHealthService()
    return _singleton
