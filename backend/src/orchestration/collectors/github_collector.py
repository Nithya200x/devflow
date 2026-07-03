import logging
from typing import Any, Dict, List

from config.config import Config
from orchestration.collectors.base_collector import BaseEvidenceCollector
from services.github_auth import PATGitHubAuth
from services.github_service import GitHubService

logger = logging.getLogger(__name__)


class GitHubEvidenceCollector(BaseEvidenceCollector):
    def __init__(self):
        super().__init__(source_name="github")
        self._service = None
        token = Config.GITHUB_TOKEN
        if token:
            try:
                auth = PATGitHubAuth(token=token)
                self._service = GitHubService(auth)
            except Exception as e:
                logger.warning(f"Failed to initialize GitHub service: {e}")

    def _parse_repo(self, context: Dict[str, Any]) -> tuple:
        repository = context.get("repository", "")
        if not repository or "/" not in repository:
            return "", ""
        parts = repository.split("/", 1)
        return parts[0], parts[1]

    def collect_evidence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self._service:
            return {
                "source": "github",
                "status": "not_configured",
                "message": "GITHUB_TOKEN not configured. Set GITHUB_TOKEN environment variable to enable GitHub evidence collection.",
            }

        owner, repo = self._parse_repo(context)
        if not owner or not repo:
            return {
                "source": "github",
                "status": "no_repository",
                "message": "No repository (owner/repo) provided in context.",
            }

        evidence: Dict[str, Any] = {
            "source": "github",
            "repository": f"{owner}/{repo}",
            "branch": context.get("branch", ""),
            "commit_sha": context.get("commit_sha", ""),
            "repo_info": {},
            "branch_info": {},
            "recent_commits": [],
            "pull_requests": [],
            "latest_release": {},
            "contributors": [],
            "languages": {},
            "topics": [],
        }

        try:
            evidence["repo_info"] = self._service.get_repo(owner, repo)
        except Exception as e:
            logger.warning("Failed to get repo info for %s/%s: %s", owner, repo, e)

        branch = context.get("branch", "")
        if branch:
            try:
                evidence["branch_info"] = self._service.get_branch(
                    owner, repo, branch
                )
            except Exception as e:
                logger.warning(
                    "Failed to get branch %s for %s/%s: %s", branch, owner, repo, e
                )

        try:
            sha = context.get("commit_sha") or branch
            evidence["recent_commits"] = self._service.get_commits(
                owner, repo, per_page=10, sha=sha or None
            )
        except Exception as e:
            logger.warning("Failed to get commits for %s/%s: %s", owner, repo, e)

        try:
            evidence["pull_requests"] = self._service.get_pull_requests(
                owner, repo, state="open", per_page=10
            )
        except Exception as e:
            logger.warning("Failed to get PRs for %s/%s: %s", owner, repo, e)

        try:
            evidence["latest_release"] = self._service.get_latest_release(
                owner, repo
            )
        except Exception as e:
            logger.warning("Failed to get latest release for %s/%s: %s", owner, repo, e)

        try:
            evidence["contributors"] = self._service.get_contributors(
                owner, repo, per_page=10
            )
        except Exception as e:
            logger.warning(
                "Failed to get contributors for %s/%s: %s", owner, repo, e
            )

        try:
            evidence["languages"] = self._service.get_languages(owner, repo)
        except Exception as e:
            logger.warning("Failed to get languages for %s/%s: %s", owner, repo, e)

        try:
            evidence["topics"] = self._service.get_topics(owner, repo)
        except Exception as e:
            logger.warning("Failed to get topics for %s/%s: %s", owner, repo, e)

        return evidence

    def collect_logs(self, context: Dict[str, Any]) -> List[str]:
        if not self._service:
            return ["GitHub: GITHUB_TOKEN not configured"]

        owner, repo = self._parse_repo(context)
        if not owner or not repo:
            return ["GitHub: No repository provided"]

        try:
            sha = context.get("commit_sha") or context.get("branch")
            commits = self._service.get_commits(
                owner, repo, per_page=20, sha=sha or None
            )
            logs = []
            for c in commits:
                commit = c.get("commit", {})
                message = commit.get("message", "").split("\n")[0]
                author = commit.get("author", {}).get("name", "unknown")
                sha_short = c.get("sha", "")[:7]
                logs.append(f"{sha_short} - {author}: {message}")
            return logs if logs else ["GitHub: No commits found"]
        except Exception as e:
            logger.warning("Failed to collect GitHub logs: %s", e)
            return [f"GitHub: Error collecting logs - {e}"]

    def collect_metadata(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self._service:
            return {
                "repository": context.get("repository", ""),
                "branch": context.get("branch", ""),
                "commit_sha": context.get("commit_sha", ""),
                "configured": False,
            }

        owner, repo = self._parse_repo(context)
        metadata: Dict[str, Any] = {
            "repository": f"{owner}/{repo}" if owner and repo else "",
            "branch": context.get("branch", ""),
            "commit_sha": context.get("commit_sha", ""),
            "configured": True,
        }

        if owner and repo:
            try:
                repo_data = self._service.get_repo(owner, repo)
                metadata["description"] = repo_data.get("description", "")
                metadata["private"] = repo_data.get("private", False)
                metadata["default_branch"] = repo_data.get("default_branch", "")
                metadata["html_url"] = repo_data.get("html_url", "")
            except Exception as e:
                logger.warning("Failed to get repo metadata: %s", e)

            branch = context.get("branch", "")
            if branch:
                try:
                    branch_data = self._service.get_branch(owner, repo, branch)
                    metadata["branch_protected"] = branch_data.get("protected", False)
                except Exception as e:
                    logger.warning("Failed to get branch metadata: %s", e)

            commit_sha = context.get("commit_sha", "")
            if commit_sha:
                try:
                    commits = self._service.get_commits(
                        owner, repo, per_page=1, sha=commit_sha
                    )
                    if commits:
                        c = commits[0]
                        metadata["commit_message"] = (
                            c.get("commit", {})
                            .get("message", "")
                            .split("\n")[0]
                        )
                        metadata["commit_author"] = (
                            c.get("commit", {})
                            .get("author", {})
                            .get("name", "")
                        )
                        metadata["commit_date"] = (
                            c.get("commit", {})
                            .get("author", {})
                            .get("date", "")
                        )
                except Exception as e:
                    logger.warning("Failed to get commit metadata: %s", e)

        return metadata

    def collect_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self._service:
            return {
                "source": "github",
                "configured": False,
            }

        owner, repo = self._parse_repo(context)
        metrics: Dict[str, Any] = {
            "source": "github",
            "configured": True,
            "open_pull_requests": 0,
            "open_issues": 0,
            "stars": 0,
            "forks": 0,
            "watchers": 0,
            "contributor_count": 0,
            "languages": {},
            "latest_release_tag": "",
        }

        if owner and repo:
            try:
                repo_data = self._service.get_repo(owner, repo)
                metrics["open_issues"] = repo_data.get("open_issues_count", 0)
                metrics["stars"] = repo_data.get("stargazers_count", 0)
                metrics["forks"] = repo_data.get("forks_count", 0)
                metrics["watchers"] = repo_data.get("watchers_count", 0)
            except Exception as e:
                logger.warning("Failed to get repo metrics: %s", e)

            try:
                prs = self._service.get_pull_requests(
                    owner, repo, state="open", per_page=1
                )
                metrics["open_pull_requests"] = len(prs)
            except Exception as e:
                logger.warning("Failed to get PR metrics: %s", e)

            try:
                contributors = self._service.get_contributors(
                    owner, repo, per_page=1
                )
                metrics["contributor_count"] = len(contributors)
            except Exception as e:
                logger.warning("Failed to get contributor metrics: %s", e)

            try:
                metrics["languages"] = self._service.get_languages(owner, repo)
            except Exception as e:
                logger.warning("Failed to get language metrics: %s", e)

            try:
                release = self._service.get_latest_release(owner, repo)
                if release:
                    metrics["latest_release_tag"] = release.get("tag_name", "")
            except Exception as e:
                logger.warning("Failed to get release metrics: %s", e)

        return metrics
