import os
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

import pytest
from unittest.mock import MagicMock, patch
from app import create_app
from extensions import db as _db
from models import User, ConnectedProject


@pytest.fixture
def app():
    application = create_app(testing=True)
    application.config['TESTING'] = True
    application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seeded_user(app):
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        if not user:
            user = User(
                name="Test User",
                email="test@example.com",
                username="testuser",
                role="developer",
                github_token="encrypted_gh_token",
            )
            user.set_password("testpass123")
            _db.session.add(user)
            _db.session.commit()
        return user


@pytest.fixture
def auth_headers(client, seeded_user):
    resp = client.post('/api/v1/auth/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    assert resp.status_code == 200
    token = resp.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def seeded_project(app, seeded_user):
    with app.app_context():
        project = ConnectedProject.query.filter_by(id=1).first()
        if not project:
            project = ConnectedProject(
                id=1,
                name="test-repo",
                github_owner="testowner",
                github_repo="test-repo",
                github_repo_id=999,
                full_name="testowner/test-repo",
                connected_by="testuser",
            )
            _db.session.add(project)
            _db.session.commit()
        return project


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
    "html_url": "https://github.com/testowner/test-repo/actions/runs/12345",
    "logs_url": "https://api.github.com/repos/testowner/test-repo/actions/runs/12345/logs",
    "jobs_url": "https://api.github.com/repos/testowner/test-repo/actions/runs/12345/jobs",
}

MOCK_JOB_RAW = {
    "id": 6789,
    "run_id": 12345,
    "name": "test",
    "status": "completed",
    "conclusion": "success",
    "started_at": "2025-01-01T00:00:00Z",
    "completed_at": "2025-01-01T00:01:30Z",
    "html_url": "https://github.com/testowner/test-repo/actions/runs/12345/job/6789",
    "steps": [
        {"name": "Checkout", "status": "completed", "conclusion": "success", "number": 1,
         "started_at": "2025-01-01T00:00:00Z", "completed_at": "2025-01-01T00:00:10Z"},
    ],
}

MOCK_GITHUB_RUNS_RESP = {"workflow_runs": [MOCK_RUN_RAW]}
MOCK_GITHUB_JOBS_RESP = {"jobs": [MOCK_JOB_RAW]}


class TestGetWorkflowRuns:
    def test_returns_runs(self, client, auth_headers, seeded_project):
        with patch("routes.pipelines.decrypt_token", return_value="ghp_fake"):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = MOCK_GITHUB_RUNS_RESP
            with patch("services.github_actions_service.requests.get", return_value=mock_resp):
                resp = client.get("/api/v1/pipelines/github/1/runs", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["id"] == 12345

    def test_returns_401_without_auth(self, client, seeded_project):
        resp = client.get("/api/v1/pipelines/github/1/runs")
        assert resp.status_code == 401

    def test_returns_404_for_nonexistent_project(self, client, auth_headers):
        resp = client.get("/api/v1/pipelines/github/999/runs", headers=auth_headers)
        assert resp.status_code == 404

    def test_returns_400_when_github_not_connected(self, client, auth_headers, app):
        with app.app_context():
            project = ConnectedProject(
                id=2, name="no-token-repo", github_owner="no", github_repo="no",
                github_repo_id=1, full_name="no/no", connected_by="testuser",
            )
            _db.session.add(project)
            _db.session.commit()
        with patch("routes.pipelines.decrypt_token", return_value=""):
            user = User.query.filter_by(username="testuser").first()
            user.github_token = ""
            _db.session.commit()
            resp = client.get("/api/v1/pipelines/github/2/runs", headers=auth_headers)
        assert resp.status_code == 400
        assert resp.get_json()["msg"] == "GitHub not connected"

    def test_returns_401_on_github_permission_error(self, client, auth_headers, seeded_project):
        with patch("routes.pipelines.decrypt_token", return_value="ghp_fake"):
            with patch("services.github_actions_service.requests.get",
                       side_effect=PermissionError("token expired")):
                resp = client.get("/api/v1/pipelines/github/1/runs", headers=auth_headers)
        assert resp.status_code == 401

    def test_returns_200_empty_on_github_404(self, client, auth_headers, seeded_project):
        with patch("routes.pipelines.decrypt_token", return_value="ghp_fake"):
            with patch("services.github_actions_service.requests.get",
                       side_effect=FileNotFoundError("not found")):
                resp = client.get("/api/v1/pipelines/github/1/runs", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["runs"] == []

    def test_returns_200_empty_on_unexpected_error(self, client, auth_headers, seeded_project):
        with patch("routes.pipelines.decrypt_token", return_value="ghp_fake"):
            with patch("services.github_actions_service.requests.get",
                       side_effect=Exception("unexpected")):
                resp = client.get("/api/v1/pipelines/github/1/runs", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["runs"] == []


class TestGetLatestRun:
    def test_returns_latest_run(self, client, auth_headers, seeded_project):
        with patch("routes.pipelines.decrypt_token", return_value="ghp_fake"):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = MOCK_GITHUB_RUNS_RESP
            with patch("services.github_actions_service.requests.get", return_value=mock_resp):
                resp = client.get("/api/v1/pipelines/github/1/latest", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["id"] == 12345

    def test_returns_empty_on_no_runs(self, client, auth_headers, seeded_project):
        with patch("routes.pipelines.decrypt_token", return_value="ghp_fake"):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"workflow_runs": []}
            with patch("services.github_actions_service.requests.get", return_value=mock_resp):
                resp = client.get("/api/v1/pipelines/github/1/latest", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json() == {}

    def test_returns_401_without_auth(self, client, seeded_project):
        resp = client.get("/api/v1/pipelines/github/1/latest")
        assert resp.status_code == 401

    def test_returns_empty_on_unexpected_error(self, client, auth_headers, seeded_project):
        with patch("routes.pipelines.decrypt_token", return_value="ghp_fake"):
            with patch("services.github_actions_service.requests.get",
                       side_effect=Exception("boom")):
                resp = client.get("/api/v1/pipelines/github/1/latest", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json() == {}


class TestGetWorkflowJobs:
    def test_returns_jobs(self, client, auth_headers, seeded_project):
        with patch("routes.pipelines.decrypt_token", return_value="ghp_fake"):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = MOCK_GITHUB_JOBS_RESP
            with patch("services.github_actions_service.requests.get", return_value=mock_resp):
                resp = client.get("/api/v1/pipelines/github/1/runs/12345/jobs", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["id"] == 6789

    def test_returns_401_without_auth(self, client, seeded_project):
        resp = client.get("/api/v1/pipelines/github/1/runs/12345/jobs")
        assert resp.status_code == 401

    def test_returns_empty_on_unexpected_error(self, client, auth_headers, seeded_project):
        with patch("routes.pipelines.decrypt_token", return_value="ghp_fake"):
            with patch("services.github_actions_service.requests.get",
                       side_effect=Exception("boom")):
                resp = client.get("/api/v1/pipelines/github/1/runs/12345/jobs", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json() == []
