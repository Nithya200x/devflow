import pytest
from unittest.mock import MagicMock, patch
from services.github_auth import PATGitHubAuth
from services.github_actions_service import GitHubActionsService, _format_run, _format_job


@pytest.fixture
def auth():
    return PATGitHubAuth("ghp_fake_token")


@pytest.fixture
def service(auth):
    return GitHubActionsService(auth)


MOCK_RUN_RAW = {
    "id": 12345,
    "name": "CI",
    "workflow_id": 42,
    "head_branch": "main",
    "head_sha": "abc123",
    "status": "completed",
    "conclusion": "success",
    "display_title": "feat: add tests",
    "actor": {"login": "testuser", "avatar_url": "https://avatars.example.com/u/1"},
    "triggering_actor": {"login": "testuser", "avatar_url": "https://avatars.example.com/u/1"},
    "event": "push",
    "run_started_at": "2025-01-01T00:00:00Z",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:01:30Z",
    "html_url": "https://github.com/owner/repo/actions/runs/12345",
    "logs_url": "https://api.github.com/repos/owner/repo/actions/runs/12345/logs",
    "jobs_url": "https://api.github.com/repos/owner/repo/actions/runs/12345/jobs",
}

MOCK_JOB_RAW = {
    "id": 6789,
    "run_id": 12345,
    "name": "test",
    "status": "completed",
    "conclusion": "success",
    "started_at": "2025-01-01T00:00:00Z",
    "completed_at": "2025-01-01T00:01:30Z",
    "html_url": "https://github.com/owner/repo/actions/runs/12345/job/6789",
    "steps": [
        {"name": "Checkout", "status": "completed", "conclusion": "success", "number": 1,
         "started_at": "2025-01-01T00:00:00Z", "completed_at": "2025-01-01T00:00:10Z"},
        {"name": "Test", "status": "completed", "conclusion": "success", "number": 2,
         "started_at": "2025-01-01T00:00:10Z", "completed_at": "2025-01-01T00:01:30Z"},
    ],
}


class TestGetWorkflowRuns:
    def test_returns_formatted_runs(self, service):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"workflow_runs": [MOCK_RUN_RAW]}
        with patch("services.github_actions_service.requests.get", return_value=mock_resp):
            runs = service.get_workflow_runs("owner", "repo")
        assert len(runs) == 1
        assert runs[0]["id"] == 12345
        assert runs[0]["conclusion"] == "success"
        assert runs[0]["actor"]["login"] == "testuser"

    def test_passes_per_page_param(self, service):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"workflow_runs": []}
        with patch("services.github_actions_service.requests.get", return_value=mock_resp) as mock_get:
            service.get_workflow_runs("owner", "repo", per_page=5)
        _, kwargs = mock_get.call_args
        assert kwargs["params"]["per_page"] == 5

    def test_returns_empty_list_when_no_runs(self, service):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"workflow_runs": []}
        with patch("services.github_actions_service.requests.get", return_value=mock_resp):
            runs = service.get_workflow_runs("owner", "repo")
        assert runs == []


class TestGetLatestRun:
    def test_returns_formatted_run(self, service):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"workflow_runs": [MOCK_RUN_RAW]}
        with patch("services.github_actions_service.requests.get", return_value=mock_resp):
            run = service.get_latest_run("owner", "repo")
        assert run["id"] == 12345
        assert run["head_branch"] == "main"

    def test_returns_empty_dict_when_no_runs(self, service):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"workflow_runs": []}
        with patch("services.github_actions_service.requests.get", return_value=mock_resp):
            run = service.get_latest_run("owner", "repo")
        assert run == {}

    def test_requests_per_page_1(self, service):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"workflow_runs": []}
        with patch("services.github_actions_service.requests.get", return_value=mock_resp) as mock_get:
            service.get_latest_run("owner", "repo")
        assert mock_get.call_args[1]["params"]["per_page"] == 1


class TestGetWorkflowJobs:
    def test_returns_formatted_jobs(self, service):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"jobs": [MOCK_JOB_RAW]}
        with patch("services.github_actions_service.requests.get", return_value=mock_resp):
            jobs = service.get_workflow_jobs("owner", "repo", 12345)
        assert len(jobs) == 1
        assert jobs[0]["id"] == 6789
        assert len(jobs[0]["steps"]) == 2
        assert jobs[0]["duration_seconds"] == 90

    def test_returns_empty_list_when_no_jobs(self, service):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"jobs": []}
        with patch("services.github_actions_service.requests.get", return_value=mock_resp):
            jobs = service.get_workflow_jobs("owner", "repo", 12345)
        assert jobs == []


class TestGetRunLogs:
    def test_returns_log_text(self, service):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "=== LOGS ===\nBuild started..."
        with patch("services.github_actions_service.requests.get", return_value=mock_resp):
            logs = service.get_run_logs("owner", "repo", 12345)
        assert "Build started" in logs

    def test_raises_on_error_status(self, service):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.raise_for_status.side_effect = Exception("HTTP 500")
        with patch("services.github_actions_service.requests.get", return_value=mock_resp):
            with pytest.raises(Exception):
                service.get_run_logs("owner", "repo", 12345)


class TestHttpGetErrors:
    def test_401_raises_permission_error(self, service):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        with patch("services.github_actions_service.requests.get", return_value=mock_resp):
            with pytest.raises(PermissionError, match="token is invalid or expired"):
                service._get("/repos/owner/repo/actions/runs")

    def test_403_raises_permission_error(self, service):
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        with patch("services.github_actions_service.requests.get", return_value=mock_resp):
            with pytest.raises(PermissionError, match="rate limit exceeded"):
                service._get("/repos/owner/repo/actions/runs")

    def test_404_raises_file_not_found(self, service):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        with patch("services.github_actions_service.requests.get", return_value=mock_resp):
            with pytest.raises(FileNotFoundError, match="GitHub resource not found"):
                service._get("/repos/owner/repo/actions/runs")

    def test_500_raises_http_error(self, service):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.raise_for_status.side_effect = Exception("500 Server Error")
        with patch("services.github_actions_service.requests.get", return_value=mock_resp):
            with pytest.raises(Exception):
                service._get("/repos/owner/repo/actions/runs")


class TestFormatRun:
    def test_formats_all_fields(self):
        result = _format_run(MOCK_RUN_RAW)
        assert result["id"] == 12345
        assert result["name"] == "CI"
        assert result["head_branch"] == "main"
        assert result["head_sha"] == "abc123"
        assert result["status"] == "completed"
        assert result["conclusion"] == "success"
        assert result["duration_seconds"] == 90
        assert result["actor"]["login"] == "testuser"

    def test_missing_actor_returns_none(self):
        raw = {**MOCK_RUN_RAW, "actor": None, "triggering_actor": None}
        result = _format_run(raw)
        assert result["actor"] is None
        assert result["triggering_actor"] is None

    def test_no_duration_when_missing_timestamps(self):
        raw = {**MOCK_RUN_RAW, "run_started_at": None, "created_at": None, "updated_at": None}
        result = _format_run(raw)
        assert result["duration_seconds"] is None


class TestFormatJob:
    def test_formats_all_fields(self):
        result = _format_job(MOCK_JOB_RAW)
        assert result["id"] == 6789
        assert result["name"] == "test"
        assert result["status"] == "completed"
        assert result["conclusion"] == "success"
        assert result["duration_seconds"] == 90
        assert len(result["steps"]) == 2

    def test_no_duration_when_missing_timestamps(self):
        raw = {**MOCK_JOB_RAW, "started_at": None, "completed_at": None}
        result = _format_job(raw)
        assert result["duration_seconds"] is None

    def test_no_steps_when_missing(self):
        raw = {**MOCK_JOB_RAW, "steps": None}
        result = _format_job(raw)
        assert result["steps"] == []

    def test_missing_step_fields(self):
        raw = {**MOCK_JOB_RAW, "steps": [{}]}
        result = _format_job(raw)
        assert result["steps"] == [{"name": None, "status": None, "conclusion": None,
                                     "number": None, "started_at": None, "completed_at": None}]
