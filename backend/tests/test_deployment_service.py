import pytest
import json
from unittest.mock import MagicMock, patch, PropertyMock, DEFAULT
from services.deployment_service import DeploymentService, DeploymentServiceError


def make_mock_deployment(**kwargs):
    from datetime import datetime, timezone
    d = MagicMock()
    d.id = kwargs.get("id", 1)
    d.deployment_id = kwargs.get("deployment_id", "dep_test")
    d.project_id = kwargs.get("project_id", 1)
    d.repository = kwargs.get("repository", "owner/repo")
    d.commit_sha = kwargs.get("commit_sha", "abc123")
    d.branch = kwargs.get("branch", "main")
    d.environment = kwargs.get("environment", "dev")
    d.status = kwargs.get("status", "building")
    d.workflow_run_id = kwargs.get("workflow_run_id", None)
    d.started_at = kwargs.get("started_at", None)
    d.completed_at = kwargs.get("completed_at", None)
    d.triggered_by = kwargs.get("triggered_by", "user1")
    d.rollback_available = kwargs.get("rollback_available", False)
    d.logs_json = kwargs.get("logs_json", "{}")
    d.deployed_by = kwargs.get("deployed_by", "user1")
    d.created_at = kwargs.get("created_at", None)
    return d


class TestDeploymentToDict:
    def test_returns_all_fields(self):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        d = make_mock_deployment(
            deployment_id="dep_dict", repository="owner/repo",
            commit_sha="abc123", branch="main", environment="prod",
            status="running", workflow_run_id=42, started_at=now,
            completed_at=None, triggered_by="user1", rollback_available=False,
            logs_json='{"key": "val"}', deployed_by="user1", created_at=now,
        )
        result = DeploymentService._deployment_to_dict(d)
        assert result["deployment_id"] == "dep_dict"
        assert result["repository"] == "owner/repo"
        assert result["commit_sha"] == "abc123"
        assert result["branch"] == "main"
        assert result["environment"] == "prod"
        assert result["status"] == "running"
        assert result["workflow_run_id"] == 42
        assert result["started_at"] is not None
        assert result["completed_at"] is None
        assert result["triggered_by"] == "user1"
        assert result["rollback_available"] is False
        assert result["logs_json"] == '{"key": "val"}'
        assert result["deployed_by"] == "user1"
        assert result["id"] == 1
        assert result["project_id"] == 1


class TestUpdateStatus:
    @patch("services.deployment_service.Deployment")
    @patch("services.deployment_service.db")
    def test_updates_status(self, mock_db, mock_deployment_cls):
        mock_filter = MagicMock()
        mock_filter.first.return_value = make_mock_deployment(
            deployment_id="dep1", status="queued"
        )
        mock_deployment_cls.query.filter_by.return_value = mock_filter

        result = DeploymentService.update_status("dep1", "building")
        assert result["status"] == "building"

    @patch("services.deployment_service.Deployment")
    @patch("services.deployment_service.db")
    def test_sets_completed_at_on_terminal_status(self, mock_db, mock_deployment_cls):
        mock_filter = MagicMock()
        mock_filter.first.return_value = make_mock_deployment(
            deployment_id="dep1", status="building"
        )
        mock_deployment_cls.query.filter_by.return_value = mock_filter

        result = DeploymentService.update_status("dep1", "success")
        assert result["status"] == "success"
        assert result["completed_at"] is not None

    @patch("services.deployment_service.Deployment")
    @patch("services.deployment_service.db")
    def test_sets_rollback_available_on_success(self, mock_db, mock_deployment_cls):
        mock_filter = MagicMock()
        mock_filter.first.return_value = make_mock_deployment(
            deployment_id="dep1", status="building"
        )
        mock_deployment_cls.query.filter_by.return_value = mock_filter

        result = DeploymentService.update_status("dep1", "success")
        assert result["rollback_available"] is True

    @patch("services.deployment_service.Deployment")
    @patch("services.deployment_service.db")
    def test_raises_on_invalid_status(self, mock_db, mock_deployment_cls):
        mock_filter = MagicMock()
        mock_filter.first.return_value = make_mock_deployment(
            deployment_id="dep1", status="queued"
        )
        mock_deployment_cls.query.filter_by.return_value = mock_filter

        with pytest.raises(DeploymentServiceError, match="Invalid status"):
            DeploymentService.update_status("dep1", "invalid_status")

    @patch("services.deployment_service.Deployment")
    @patch("services.deployment_service.db")
    def test_updates_workflow_run_id(self, mock_db, mock_deployment_cls):
        mock_filter = MagicMock()
        mock_filter.first.return_value = make_mock_deployment(
            deployment_id="dep1", status="building"
        )
        mock_deployment_cls.query.filter_by.return_value = mock_filter

        result = DeploymentService.update_status("dep1", "success", workflow_run_id=42)
        assert result["workflow_run_id"] == 42

    @patch("services.deployment_service.Deployment")
    @patch("services.deployment_service.db")
    def test_updates_logs(self, mock_db, mock_deployment_cls):
        mock_filter = MagicMock()
        mock_filter.first.return_value = make_mock_deployment(
            deployment_id="dep1", status="building", logs_json="{}"
        )
        mock_deployment_cls.query.filter_by.return_value = mock_filter

        result = DeploymentService.update_status("dep1", "success", logs={"build_url": "https://..."})
        assert "build_url" in json.loads(result["logs_json"])


class TestGetAll:
    @patch("services.deployment_service.Deployment")
    def test_returns_all_deployments_descending(self, mock_deployment_cls):
        mock_deployment_cls.query.order_by.return_value.all.return_value = [
            make_mock_deployment(id=2, deployment_id="dep2"),
            make_mock_deployment(id=1, deployment_id="dep1"),
        ]
        deps = DeploymentService.get_all()
        assert len(deps) == 2
        assert deps[0]["deployment_id"] == "dep2"

    @patch("services.deployment_service.Deployment")
    def test_filters_by_project_id(self, mock_deployment_cls):
        mock_deployment_cls.query.filter_by.return_value.order_by.return_value.all.return_value = [
            make_mock_deployment(project_id=1, deployment_id="dep1"),
        ]
        deps = DeploymentService.get_all(project_id=1)
        assert len(deps) == 1
        assert deps[0]["project_id"] == 1

    @patch("services.deployment_service.Deployment")
    def test_returns_empty_when_no_deployments(self, mock_deployment_cls):
        mock_deployment_cls.query.order_by.return_value.all.return_value = []
        deps = DeploymentService.get_all()
        assert deps == []


class TestTriggerDeployment:
    @patch("services.deployment_service.User")
    @patch("services.deployment_service.DeploymentService._get_gh_actions")
    @patch("services.deployment_service.db")
    @patch("services.deployment_service.Deployment")
    @patch("services.deployment_service.ConnectedProject")
    def test_creates_deployment_and_triggers_workflow(
        self, mock_project_cls, mock_deployment_cls, mock_db, mock_get_gh, mock_user_cls,
    ):
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.github_owner = "owner"
        mock_project.github_repo = "repo"
        mock_project.full_name = "owner/repo"
        mock_project_filter = MagicMock()
        mock_project_filter.first.return_value = mock_project
        mock_project_cls.query.filter_by.return_value = mock_project_filter

        mock_user_filter = MagicMock()
        mock_user_filter.first.return_value = MagicMock()
        mock_user_cls.query.filter_by.return_value = mock_user_filter

        mock_gh = MagicMock()
        mock_get_gh.return_value = mock_gh

        def _make_deployment(**kwargs):
            return make_mock_deployment(**kwargs)

        mock_deployment_cls.side_effect = _make_deployment

        result = DeploymentService.trigger_deployment(
            project_id=1, branch="main", commit_sha="abc123",
            environment="dev", triggered_by="testuser",
        )

        assert result["branch"] == "main"
        assert result["commit_sha"] == "abc123"
        assert result["environment"] == "dev"
        assert result["repository"] == "owner/repo"
        assert result["triggered_by"] == "testuser"
        assert result["project_id"] == 1

        mock_gh.trigger_workflow_dispatch.assert_called_once_with(
            owner="owner", repo="repo", workflow_id="deploy.yml",
            ref="main", inputs={"environment": "dev", "commit_sha": "abc123"},
        )

    @patch("services.deployment_service.User")
    @patch("services.deployment_service.DeploymentService._get_gh_actions")
    @patch("services.deployment_service.db")
    @patch("services.deployment_service.Deployment")
    @patch("services.deployment_service.ConnectedProject")
    def test_sets_failed_status_on_workflow_error(
        self, mock_project_cls, mock_deployment_cls, mock_db, mock_get_gh, mock_user_cls,
    ):
        mock_project = MagicMock()
        mock_project.id = 2
        mock_project.github_owner = "owner"
        mock_project.github_repo = "repo"
        mock_project.full_name = "owner/repo"
        mock_project_filter = MagicMock()
        mock_project_filter.first.return_value = mock_project
        mock_project_cls.query.filter_by.return_value = mock_project_filter

        mock_user_filter = MagicMock()
        mock_user_filter.first.return_value = MagicMock()
        mock_user_cls.query.filter_by.return_value = mock_user_filter

        mock_gh = MagicMock()
        mock_gh.trigger_workflow_dispatch.side_effect = Exception("API error")
        mock_get_gh.return_value = mock_gh

        with pytest.raises(DeploymentServiceError, match="Failed to trigger deployment"):
            DeploymentService.trigger_deployment(
                project_id=2, branch="main", commit_sha="abc",
                environment="dev", triggered_by="testuser",
            )

    @patch("services.deployment_service.User")
    @patch("services.deployment_service.DeploymentService._get_gh_actions")
    @patch("services.deployment_service.db")
    @patch("services.deployment_service.Deployment")
    @patch("services.deployment_service.ConnectedProject")
    def test_resolves_empty_commit_via_github_api(
        self, mock_project_cls, mock_deployment_cls, mock_db, mock_get_gh, mock_user_cls,
    ):
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.github_owner = "owner"
        mock_project.github_repo = "repo"
        mock_project.full_name = "owner/repo"
        mock_project_filter = MagicMock()
        mock_project_filter.first.return_value = mock_project
        mock_project_cls.query.filter_by.return_value = mock_project_filter

        mock_user_filter = MagicMock()
        mock_user_filter.first.return_value = MagicMock()
        mock_user_cls.query.filter_by.return_value = mock_user_filter

        mock_gh = MagicMock()
        mock_gh.get_commit_sha.return_value = "resolved_sha_abc123"
        mock_get_gh.return_value = mock_gh

        def _make_deployment(**kwargs):
            return make_mock_deployment(**kwargs)

        mock_deployment_cls.side_effect = _make_deployment

        result = DeploymentService.trigger_deployment(
            project_id=1, branch="main", commit_sha="",
            environment="dev", triggered_by="testuser",
        )

        assert result["commit_sha"] == "resolved_sha_abc123"
        mock_gh.get_commit_sha.assert_called_once_with("owner", "repo", "main")
        mock_gh.trigger_workflow_dispatch.assert_called_once_with(
            owner="owner", repo="repo", workflow_id="deploy.yml",
            ref="main", inputs={"environment": "dev", "commit_sha": "resolved_sha_abc123"},
        )

    @patch("services.deployment_service.ConnectedProject")
    def test_raises_when_project_not_found(self, mock_project_cls):
        mock_project_filter = MagicMock()
        mock_project_filter.first.return_value = None
        mock_project_cls.query.filter_by.return_value = mock_project_filter

        with pytest.raises(DeploymentServiceError, match="Project not found"):
            DeploymentService.trigger_deployment(
                project_id=999, branch="main", commit_sha="abc",
                environment="dev", triggered_by="testuser",
            )


class TestRollbackDeployment:
    @patch("services.deployment_service.DeploymentService._get_k8s")
    @patch("services.deployment_service.db")
    @patch("services.deployment_service.Deployment")
    @patch("services.deployment_service.ConnectedProject")
    def test_creates_rollback_deployment(
        self, mock_project_cls, mock_deployment_cls, mock_db, mock_get_k8s,
    ):
        mock_project = MagicMock()
        mock_project.id = 3
        mock_project.repository = "owner/repo"
        mock_project.commit_sha = "abc123"
        mock_project.branch = "main"
        mock_project.environment = "dev"
        mock_project.kubernetes_namespace = "devflow"
        mock_project.kubernetes_deployment = "backend"
        mock_project_filter = MagicMock()
        mock_project_filter.first.return_value = mock_project
        mock_project_cls.query.filter_by.return_value = mock_project_filter

        mock_dep = make_mock_deployment(
            id=1, deployment_id="dep_orig", project_id=3,
            status="success", commit_sha="abc123", branch="main", environment="dev",
        )
        mock_deployment_cls.query.get_or_404.return_value = mock_dep

        mock_k8s = MagicMock()
        mock_get_k8s.return_value = mock_k8s
        mock_k8s.get_deployment.return_value = {
            "containers": [{"name": "backend", "image": "devflow-backend:latest"}],
        }
        mock_k8s.patch_deployment.return_value = {"success": True}

        def make_deployment(**kwargs):
            d = make_mock_deployment(**kwargs)
            return d

        mock_deployment_cls.side_effect = make_deployment

        result = DeploymentService.rollback_deployment(1, "testuser")
        assert result["triggered_by"] == "testuser"
        mock_k8s.patch_deployment.assert_called_once()

    @patch("services.deployment_service.Deployment")
    @patch("services.deployment_service.ConnectedProject")
    def test_raises_when_no_k8s_configured(self, mock_project_cls, mock_deployment_cls):
        mock_project = MagicMock()
        mock_project.id = 4
        mock_project.kubernetes_namespace = ""
        mock_project.kubernetes_deployment = ""
        mock_project_filter = MagicMock()
        mock_project_filter.first.return_value = mock_project
        mock_project_cls.query.filter_by.return_value = mock_project_filter

        mock_dep = make_mock_deployment(id=2, deployment_id="dep_nok8s", project_id=4)
        mock_deployment_cls.query.get_or_404.return_value = mock_dep

        with pytest.raises(DeploymentServiceError, match="Project has no Kubernetes deployment configured"):
            DeploymentService.rollback_deployment(2, "testuser")


class TestGetRolloutStatus:
    @patch("services.deployment_service.Deployment")
    @patch("services.deployment_service.ConnectedProject")
    @patch("services.deployment_service.KubernetesService")
    def test_returns_rollout_status(
        self, mock_k8s_cls, mock_project_cls, mock_deployment_cls,
    ):
        mock_project = MagicMock()
        mock_project.id = 5
        mock_project.kubernetes_namespace = "devflow"
        mock_project.kubernetes_deployment = "backend"
        mock_project_filter = MagicMock()
        mock_project_filter.first.return_value = mock_project
        mock_project_cls.query.filter_by.return_value = mock_project_filter

        mock_dep = make_mock_deployment(id=3, deployment_id="dep_rollout", project_id=5)
        mock_deployment_cls.query.get_or_404.return_value = mock_dep

        mock_k8s = MagicMock()
        mock_k8s_cls.return_value = mock_k8s
        mock_k8s.get_rollout_status.return_value = {
            "deployment": "backend", "namespace": "devflow",
            "desired_replicas": 3, "available_replicas": 3, "status": "complete",
        }

        result = DeploymentService.get_rollout_status(3)
        assert result["status"] == "complete"
        assert result["available_replicas"] == 3

    @patch("services.deployment_service.Deployment")
    @patch("services.deployment_service.ConnectedProject")
    def test_returns_not_configured_when_no_k8s(self, mock_project_cls, mock_deployment_cls):
        mock_project = MagicMock()
        mock_project.id = 6
        mock_project.kubernetes_namespace = ""
        mock_project.kubernetes_deployment = ""
        mock_project_filter = MagicMock()
        mock_project_filter.first.return_value = mock_project
        mock_project_cls.query.filter_by.return_value = mock_project_filter

        mock_dep = make_mock_deployment(id=4, deployment_id="dep_nok8s2", project_id=6)
        mock_deployment_cls.query.get_or_404.return_value = mock_dep

        result = DeploymentService.get_rollout_status(4)
        assert result["status"] == "not_configured"
