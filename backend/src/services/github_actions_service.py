import requests
import logging
from services.github_auth import BaseGitHubAuth

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


class GitHubActionsService:
    def __init__(self, auth: BaseGitHubAuth):
        self.auth = auth

    def _headers(self) -> dict:
        h = self.auth.get_auth_headers()
        h["Accept"] = "application/vnd.github.v3+json"
        return h

    def _get(self, path: str, params: dict = None) -> dict:
        url = f"{GITHUB_API_BASE}{path}"
        resp = requests.get(url, headers=self._headers(), params=params, timeout=30)
        if resp.status_code == 401:
            logger.warning("GitHub API 401 – token may be invalid or expired")
            raise PermissionError("GitHub token is invalid or expired")
        if resp.status_code == 403:
            logger.warning("GitHub API 403 – rate limit exceeded")
            raise PermissionError("GitHub API rate limit exceeded")
        if resp.status_code == 404:
            raise FileNotFoundError(f"GitHub resource not found: {path}")
        resp.raise_for_status()
        return resp.json()

    def get_workflow_runs(self, owner: str, repo: str, per_page: int = 20) -> list:
        params = {"per_page": per_page}
        data = self._get(f"/repos/{owner}/{repo}/actions/runs", params=params)
        return [_format_run(r) for r in data.get("workflow_runs", [])]

    def get_latest_run(self, owner: str, repo: str) -> dict:
        params = {"per_page": 1}
        data = self._get(f"/repos/{owner}/{repo}/actions/runs", params=params)
        runs = data.get("workflow_runs", [])
        if not runs:
            return {}
        return _format_run(runs[0])

    def get_workflow_jobs(self, owner: str, repo: str, run_id: int) -> list:
        data = self._get(f"/repos/{owner}/{repo}/actions/runs/{run_id}/jobs")
        return [_format_job(j) for j in data.get("jobs", [])]

    def get_run_logs(self, owner: str, repo: str, run_id: int) -> str:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/actions/runs/{run_id}/logs"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.text

    def trigger_workflow_dispatch(
        self, owner: str, repo: str, workflow_id: str = "deploy.yml",
        ref: str = "main", inputs: dict = None
    ) -> int:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"
        body = {"ref": ref}
        if inputs:
            body["inputs"] = inputs
        resp = requests.post(url, headers=self._headers(), json=body, timeout=30)
        if resp.status_code == 204:
            logger.info("Workflow dispatch triggered for %s/%s: ref=%s inputs=%s", owner, repo, ref, inputs)
            return resp.status_code
        if resp.status_code == 401:
            raise PermissionError("GitHub token is invalid or expired")
        if resp.status_code == 403:
            raise PermissionError("GitHub API rate limit exceeded or workflow disabled")
        if resp.status_code == 404:
            raise FileNotFoundError(f"Workflow {workflow_id} not found in {owner}/{repo}")
        resp.raise_for_status()
        return resp.status_code


def _format_run(r: dict) -> dict:
    created = r.get("run_started_at") or r.get("created_at", "")
    duration = None
    if r.get("updated_at") and created:
        from datetime import datetime
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        try:
            start = datetime.strptime(created, fmt)
            end = datetime.strptime(r["updated_at"], fmt)
            duration = int((end - start).total_seconds())
        except Exception:
            pass
    return {
        "id": r.get("id"),
        "name": r.get("name"),
        "workflow_id": r.get("workflow_id"),
        "head_branch": r.get("head_branch"),
        "head_sha": r.get("head_sha"),
        "status": r.get("status"),
        "conclusion": r.get("conclusion"),
        "display_title": r.get("display_title"),
        "actor": {
            "login": r.get("actor", {}).get("login", ""),
            "avatar_url": r.get("actor", {}).get("avatar_url", ""),
        } if r.get("actor") else None,
        "triggering_actor": {
            "login": r.get("triggering_actor", {}).get("login", ""),
            "avatar_url": r.get("triggering_actor", {}).get("avatar_url", ""),
        } if r.get("triggering_actor") else None,
        "event": r.get("event"),
        "created_at": created,
        "updated_at": r.get("updated_at"),
        "duration_seconds": duration,
        "html_url": r.get("html_url"),
        "logs_url": r.get("logs_url"),
        "jobs_url": r.get("jobs_url"),
    }


def _format_job(j: dict) -> dict:
    duration = None
    if j.get("started_at") and j.get("completed_at"):
        from datetime import datetime
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        try:
            start = datetime.strptime(j["started_at"], fmt)
            end = datetime.strptime(j["completed_at"], fmt)
            duration = int((end - start).total_seconds())
        except Exception:
            pass
    steps = []
    for s in (j.get("steps") or []):
        steps.append({
            "name": s.get("name"),
            "status": s.get("status"),
            "conclusion": s.get("conclusion"),
            "number": s.get("number"),
            "started_at": s.get("started_at"),
            "completed_at": s.get("completed_at"),
        })
    return {
        "id": j.get("id"),
        "run_id": j.get("run_id"),
        "name": j.get("name"),
        "status": j.get("status"),
        "conclusion": j.get("conclusion"),
        "started_at": j.get("started_at"),
        "completed_at": j.get("completed_at"),
        "duration_seconds": duration,
        "steps": steps,
        "html_url": j.get("html_url"),
    }
