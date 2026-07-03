import logging
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests

from config.config import Config

logger = logging.getLogger(__name__)


class JenkinsError(Exception):
    def __init__(self, message: str, status_code: int = 500, details: Any = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class JenkinsConfigError(JenkinsError):
    def __init__(self, missing: List[str]):
        msg = f"Jenkins not configured: missing {', '.join(missing)}"
        super().__init__(msg, status_code=503)


class JenkinsOfflineError(JenkinsError):
    def __init__(self, details: str = ""):
        msg = "Unable to connect to Jenkins."
        super().__init__(msg, status_code=503, details=details)


class JenkinsTimeoutError(JenkinsError):
    def __init__(self, details: str = ""):
        msg = "Jenkins request timed out."
        super().__init__(msg, status_code=504, details=details)


REQUEST_EXCEPTIONS = (
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
)


class JenkinsService:
    def __init__(self):
        self._base_url = Config.JENKINS_URL.rstrip("/")
        self._username = Config.JENKINS_USERNAME or Config.JENKINS_USER
        self._api_token = Config.JENKINS_API_TOKEN or Config.JENKINS_TOKEN
        self._job_name = Config.JENKINS_JOB_NAME
        self._crumb: Optional[str] = None
        self._crumb_request_field: Optional[str] = None
        self._last_successful_connection: Optional[float] = None
        self._session = requests.Session()
        self._session.auth = (self._username, self._api_token)
        self._session.headers.update({"Content-Type": "application/json"})
        self._max_retries = 3

    def _check_config(self):
        missing = []
        if not self._base_url:
            missing.append("JENKINS_URL")
        if not self._username:
            missing.append("JENKINS_USERNAME")
        if not self._api_token:
            missing.append("JENKINS_API_TOKEN")
        if missing:
            raise JenkinsConfigError(missing)

    def _get_crumb(self):
        try:
            resp = self._session.get(
                f"{self._base_url}/crumbIssuer/api/json", timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                self._crumb = data.get("crumb")
                self._crumb_request_field = data.get("crumbRequestField", "Jenkins-Crumb")
        except Exception as e:
            logger.warning(f"Failed to fetch Jenkins crumb: {e}")

    def _request(
        self, method: str, path: str, **kwargs
    ) -> requests.Response:
        self._check_config()
        url = f"{self._base_url}{path}"
        kwargs.setdefault("timeout", 30)
        headers = kwargs.pop("headers", {})
        if self._crumb:
            headers[self._crumb_request_field or "Jenkins-Crumb"] = self._crumb
        if headers:
            kwargs["headers"] = headers

        last_exception = None
        for attempt in range(1, self._max_retries + 1):
            start = time.time()
            try:
                resp = self._session.request(method, url, **kwargs)
                elapsed = time.time() - start
                self._log_request(method, url, resp.status_code, elapsed, attempt)
                if resp.status_code in (502, 503, 504) and attempt < self._max_retries:
                    self._sleep_before_retry(attempt, resp.status_code)
                    continue
                self._last_successful_connection = time.time()
                return resp
            except requests.exceptions.ConnectionError as e:
                elapsed = time.time() - start
                self._log_request(method, url, "CONNECTION_ERROR", elapsed, attempt, error=str(e))
                if attempt < self._max_retries:
                    self._sleep_before_retry(attempt, 0)
                    continue
                raise JenkinsOfflineError(details=str(e)) from e
            except requests.exceptions.Timeout as e:
                elapsed = time.time() - start
                self._log_request(method, url, "TIMEOUT", elapsed, attempt, error=str(e))
                if attempt < self._max_retries:
                    self._sleep_before_retry(attempt, 0)
                    continue
                raise JenkinsTimeoutError(details=str(e)) from e
            except requests.exceptions.RequestException as e:
                elapsed = time.time() - start
                self._log_request(method, url, "REQUEST_ERROR", elapsed, attempt, error=str(e))
                raise JenkinsError(f"Jenkins request failed: {e}", details=str(e)) from e
        raise last_exception or JenkinsError("Max retries exceeded")

    def _sleep_before_retry(self, attempt: int, status_code: int):
        delay = min(2 ** attempt, 15)
        logger.info(f"Retrying after {delay}s (attempt {attempt}/{self._max_retries}, status={status_code})")
        time.sleep(delay)

    def _log_request(
        self,
        method: str,
        url: str,
        status: Any,
        elapsed: float,
        attempt: int,
        error: str = "",
    ):
        log_line = (
            f"[JENKINS] {method} {url} -> {status} "
            f"({elapsed * 1000:.0f}ms attempt={attempt}/{self._max_retries})"
        )
        if error:
            log_line += f" error={error}"
        logger.info(log_line)

    def _handle_response(self, resp: requests.Response) -> Any:
        if resp.status_code == 401:
            raise JenkinsError("Jenkins authentication failed", 401)
        if resp.status_code == 403:
            raise JenkinsError("Jenkins access denied", 403)
        if resp.status_code == 404:
            raise JenkinsError("Jenkins resource not found", 404)
        if resp.status_code >= 500:
            raise JenkinsError(f"Jenkins server error: {resp.status_code}", resp.status_code)
        try:
            return resp.json() if resp.text and resp.headers.get("Content-Type", "").startswith("application/json") else resp.text
        except ValueError:
            return resp.text

    # ── Public API ──────────────────────────────────────────────

    def trigger_build(
        self,
        repository_name: str = "",
        branch: str = "",
        commit_sha: str = "",
        triggered_by: str = "",
    ) -> Dict[str, Any]:
        self._check_config()
        self._get_crumb()
        job_path = f"/job/{quote(self._job_name)}"
        params = {
            "REPOSITORY_NAME": repository_name,
            "BRANCH": branch or "main",
            "COMMIT_SHA": commit_sha or "",
            "TRIGGERED_BY": triggered_by or "",
        }
        resp = self._request(
            "POST",
            f"{job_path}/buildWithParameters",
            params=params,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status_code == 400:
            logger.info("buildWithParameters not supported (no parameters defined), falling back to build")
            resp = self._request(
                "POST",
                f"{job_path}/build",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if resp.status_code not in (200, 201, 302):
            raise JenkinsError(
                f"Failed to trigger build: HTTP {resp.status_code}",
                resp.status_code,
            )
        queue_url = resp.headers.get("Location", "")
        queue_id = ""
        if queue_url:
            try:
                queue_id = queue_url.rstrip("/").split("/")[-1]
            except IndexError:
                pass
        return {
            "queue_id": queue_id,
            "queue_url": queue_url,
            "job_name": self._job_name,
            "status": "queued",
            "timestamp": time.time(),
        }

    def get_queue_status(self, queue_id: str) -> Dict[str, Any]:
        resp = self._request("GET", f"/queue/item/{queue_id}/api/json")
        data = self._handle_response(resp)
        if isinstance(data, str):
            return {"queue_id": queue_id, "status": "unknown", "raw": data}
        why = data.get("why", "")
        executable = data.get("executable")
        build_number = None
        if executable:
            build_number = executable.get("number")
        return {
            "queue_id": queue_id,
            "status": "queued" if not executable else "running",
            "why": why,
            "build_number": build_number,
            "timestamp": time.time(),
        }

    def get_build_info(self, build_number: int) -> Dict[str, Any]:
        job_path = f"/job/{quote(self._job_name)}"
        resp = self._request("GET", f"{job_path}/{build_number}/api/json")
        data = self._handle_response(resp)
        if isinstance(data, str):
            return {"build_number": build_number, "status": "unknown"}
        building = data.get("building", False)
        result = data.get("result")
        if building:
            status = "running"
        elif result == "SUCCESS":
            status = "success"
        elif result == "FAILURE":
            status = "failed"
        elif result == "ABORTED":
            status = "aborted"
        elif result == "UNSTABLE":
            status = "unstable"
        else:
            status = (result or "unknown").lower()
        duration_ms = data.get("duration", 0)
        return {
            "build_number": build_number,
            "status": status,
            "result": result,
            "building": building,
            "duration_ms": duration_ms,
            "duration_seconds": duration_ms / 1000 if duration_ms else 0,
            "timestamp": data.get("timestamp"),
            "url": data.get("url", ""),
            "display_name": data.get("fullDisplayName", ""),
            "parameters": {
                p.get("name", ""): p.get("value", "")
                for p in data.get("actions", [{}])[0].get("parameters", [])
            } if data.get("actions") else {},
        }

    def get_build_status(self, build_number: int) -> Dict[str, Any]:
        return self.get_build_info(build_number)

    def get_console_output(self, build_number: int) -> Dict[str, Any]:
        job_path = f"/job/{quote(self._job_name)}"
        resp = self._request("GET", f"{job_path}/{build_number}/consoleText")
        text = resp.text if resp.status_code == 200 else ""
        return {
            "build_number": build_number,
            "console_text": text,
            "truncated": len(text) > 50000,
        }

    def health_check(self) -> Dict[str, Any]:
        self._check_config()
        errors = []
        info = {}
        info["server_url"] = self._base_url
        info["configured_job"] = self._job_name
        info["authenticated_user"] = self._username
        info["config_valid"] = True
        info["last_successful_connection"] = self._last_successful_connection

        # Server check
        server_start = time.time()
        try:
            resp = self._request("GET", "/api/json")
            data = self._handle_response(resp)
            server_elapsed = time.time() - server_start
            info["response_time_ms"] = round(server_elapsed * 1000, 1)
            if isinstance(data, dict):
                info["server_version"] = data.get("nodeDescription", "unknown")
                info["node_name"] = data.get("nodeName", "")
        except JenkinsError as e:
            errors.append(e.message)
            info["error"] = e.message
            info["response_time_ms"] = None

        # Job check
        job_start = time.time()
        try:
            job_path = f"/job/{quote(self._job_name)}/api/json"
            resp_job = self._request("GET", job_path)
            job_data = self._handle_response(resp_job)
            job_elapsed = time.time() - job_start
            info["job_response_time_ms"] = round(job_elapsed * 1000, 1)
            if isinstance(job_data, dict):
                info["job_exists"] = True
                info["job_name"] = self._job_name
                info["job_url"] = job_data.get("url", "")
                info["job_description"] = job_data.get("description", "")
                info["last_build"] = job_data.get("lastBuild", {}).get("number") if isinstance(job_data.get("lastBuild"), dict) else None
                info["last_completed_build"] = job_data.get("lastCompletedBuild", {}).get("number") if isinstance(job_data.get("lastCompletedBuild"), dict) else None
                info["last_failed_build"] = job_data.get("lastFailedBuild", {}).get("number") if isinstance(job_data.get("lastFailedBuild"), dict) else None
            else:
                info["job_exists"] = True
                info["job_name"] = self._job_name
        except JenkinsError:
            errors.append(f"Job '{self._job_name}' not found")
            info["job_exists"] = False

        return {
            "connected": len(errors) == 0,
            "authenticated_user": self._username,
            "server_url": self._base_url,
            **info,
            "errors": errors if errors else None,
        }

    def get_build_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        job_path = f"/job/{quote(self._job_name)}"
        url = f"{job_path}/api/json?tree=builds[number,building,result,duration,timestamp,fullDisplayName,url]{{{0},{limit}}}"
        resp = self._request("GET", url)
        data = self._handle_response(resp)
        if isinstance(data, str):
            return []
        builds = data.get("builds", [])
        result = []
        for b in builds:
            number = b.get("number")
            building = b.get("building", False)
            result_status = b.get("result")
            if building:
                status = "running"
            elif result_status == "SUCCESS":
                status = "success"
            elif result_status == "FAILURE":
                status = "failed"
            elif result_status == "ABORTED":
                status = "aborted"
            elif result_status == "UNSTABLE":
                status = "unstable"
            else:
                status = (result_status or "unknown").lower()
            result.append({
                "build_number": number,
                "status": status,
                "result": result_status,
                "building": building,
                "duration_ms": b.get("duration", 0),
                "duration_seconds": (b.get("duration", 0) or 0) / 1000,
                "timestamp": b.get("timestamp"),
                "url": b.get("url", ""),
                "display_name": b.get("fullDisplayName", ""),
            })
        return result
