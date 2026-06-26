import requests
import logging
from services.github_auth import BaseGitHubAuth

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"

class GitHubService:
    def __init__(self, auth: BaseGitHubAuth):
        self.auth = auth

    def _headers(self) -> dict:
        h = self.auth.get_auth_headers()
        h["Accept"] = "application/vnd.github.v3+json"
        return h

    def _get(self, path: str, params: dict = None) -> dict:
        url = f"{GITHUB_API_BASE}{path}"
        resp = requests.get(url, headers=self._headers(), params=params, timeout=15)
        if resp.status_code == 401:
            logger.warning("GitHub API 401 – token may be invalid or expired")
            raise PermissionError("GitHub token is invalid or expired")
        if resp.status_code == 403:
            logger.warning("GitHub API 403 – rate limit exceeded")
            raise PermissionError("GitHub API rate limit exceeded. Check rate limit at https://api.github.com/rate_limit")
        if resp.status_code == 404:
            raise FileNotFoundError(f"GitHub resource not found: {path}")
        resp.raise_for_status()
        return resp.json()

    def get_user(self) -> dict:
        return self._get("/user")

    def get_repos(self, per_page: int = 50) -> list:
        return self._get("/user/repos", params={"per_page": per_page, "sort": "updated", "type": "all"})

    def get_repo(self, owner: str, repo: str) -> dict:
        return self._get(f"/repos/{owner}/{repo}")

    def get_commits(self, owner: str, repo: str, per_page: int = 20, sha: str = None) -> list:
        params = {"per_page": per_page}
        if sha:
            params["sha"] = sha
        return self._get(f"/repos/{owner}/{repo}/commits", params=params)

    def get_branches(self, owner: str, repo: str) -> list:
        return self._get(f"/repos/{owner}/{repo}/branches")

    def get_branch(self, owner: str, repo: str, branch: str) -> dict:
        return self._get(f"/repos/{owner}/{repo}/branches/{branch}")

    def get_pull_requests(self, owner: str, repo: str, state: str = "all", per_page: int = 20) -> list:
        return self._get(f"/repos/{owner}/{repo}/pulls", params={"state": state, "per_page": per_page, "sort": "updated"})

    def get_contributors(self, owner: str, repo: str, per_page: int = 20) -> list:
        return self._get(f"/repos/{owner}/{repo}/contributors", params={"per_page": per_page})

    def get_latest_release(self, owner: str, repo: str) -> dict:
        try:
            return self._get(f"/repos/{owner}/{repo}/releases/latest")
        except Exception:
            return {}

    def get_languages(self, owner: str, repo: str) -> dict:
        return self._get(f"/repos/{owner}/{repo}/languages")

    def get_topics(self, owner: str, repo: str) -> list:
        try:
            h = self._headers()
            h["Accept"] = "application/vnd.github.mercy-preview+json"
            url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/topics"
            resp = requests.get(url, headers=h, timeout=15)
            resp.raise_for_status()
            return resp.json().get("names", [])
        except Exception:
            return []

    def get_repo_stats(self, owner: str, repo: str) -> dict:
        repo_data = self.get_repo(owner, repo)
        languages = self.get_languages(owner, repo)
        topics = self.get_topics(owner, repo)
        return {
            "repo": repo_data,
            "languages": languages,
            "topics": topics
        }
