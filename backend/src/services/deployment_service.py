import json
import logging
import os
from datetime import datetime, timezone

from extensions import db
from models import Deployment, ConnectedProject, User
from utils.time import now, to_iso
from utils.encryption import decrypt_token
from services.github_auth import PATGitHubAuth
from services.github_actions_service import GitHubActionsService
from services.kubernetes_service import KubernetesService

logger = logging.getLogger(__name__)


class DeploymentServiceError(Exception):
    pass


DEPLOYMENT_STATUSES = [
    "queued", "building", "deploying", "success", "failed", "rolled_back",
]


class DeploymentService:

    @staticmethod
    def _get_gh_actions(user: User) -> GitHubActionsService:
        if not user or not user.github_token:
            raise DeploymentServiceError("GitHub not connected")
        token = decrypt_token(user.github_token)
        auth = PATGitHubAuth(token)
        return GitHubActionsService(auth)

    @staticmethod
    def _get_k8s() -> KubernetesService:
        ks = KubernetesService()
        ks.connect()
        return ks

    @staticmethod
    def trigger_deployment(
        project_id: int,
        branch: str,
        commit_sha: str,
        environment: str,
        triggered_by: str,
    ) -> dict:
        project = ConnectedProject.query.filter_by(id=project_id).first()
        if not project:
            raise DeploymentServiceError("Project not found")
        if not project.github_owner or not project.github_repo:
            raise DeploymentServiceError("Project has no GitHub repository configured")

        user = User.query.filter_by(username=triggered_by).first()
        gh = DeploymentService._get_gh_actions(user)

        if not commit_sha:
            commit_sha = gh.get_commit_sha(project.github_owner, project.github_repo, branch)

        dep = Deployment(
            project_id=project.id,
            repository=project.full_name,
            commit_sha=commit_sha,
            branch=branch,
            environment=environment,
            status="queued",
            triggered_by=triggered_by,
            started_at=now(),
        )
        db.session.add(dep)
        db.session.commit()

        try:
            gh.trigger_workflow_dispatch(
                owner=project.github_owner,
                repo=project.github_repo,
                workflow_id="deploy.yml",
                ref=branch,
                inputs={
                    "environment": environment,
                    "commit_sha": commit_sha,
                },
            )
            dep.status = "building"
            db.session.commit()
            logger.info(
                "Deployment %s triggered: %s/%s ref=%s env=%s",
                dep.deployment_id, project.github_owner, project.github_repo, branch, environment,
            )
        except Exception as e:
            dep.status = "failed"
            dep.logs_json = json.dumps({"error": str(e)})
            db.session.commit()
            logger.error("Failed to trigger workflow dispatch: %s", e)
            raise DeploymentServiceError(f"Failed to trigger deployment: {e}")

        return DeploymentService._deployment_to_dict(dep)

    @staticmethod
    def get_all(project_id: int = None) -> list:
        query = Deployment.query
        if project_id is not None:
            query = query.filter_by(project_id=project_id)
        deployments = query.order_by(Deployment.created_at.desc()).all()
        return [DeploymentService._deployment_to_dict(d) for d in deployments]

    @staticmethod
    def get_by_id(deployment_id: int) -> dict:
        dep = Deployment.query.get_or_404(deployment_id)
        return DeploymentService._deployment_to_dict(dep)

    @staticmethod
    def get_by_deployment_id(deployment_id: str) -> dict:
        dep = Deployment.query.filter_by(deployment_id=deployment_id).first()
        if not dep:
            raise DeploymentServiceError("Deployment not found")
        return DeploymentService._deployment_to_dict(dep)

    @staticmethod
    def rollback_deployment(deployment_id: int, triggered_by: str) -> dict:
        dep = Deployment.query.get_or_404(deployment_id)
        project = ConnectedProject.query.filter_by(id=dep.project_id).first()
        if not project:
            raise DeploymentServiceError("Project not found")

        k8s = DeploymentService._get_k8s()
        ns = project.kubernetes_namespace
        dep_name = project.kubernetes_deployment

        if not ns or not dep_name:
            raise DeploymentServiceError("Project has no Kubernetes deployment configured")

        current = k8s.get_deployment(dep_name, ns)
        if not current:
            raise DeploymentServiceError(f"Deployment {ns}/{dep_name} not found in cluster")

        current_image = current["containers"][0]["image"] if current.get("containers") else ""

        rollback_dep = Deployment(
            project_id=dep.project_id,
            repository=dep.repository,
            commit_sha=dep.commit_sha,
            branch=dep.branch,
            environment=dep.environment,
            status="deploying",
            triggered_by=triggered_by,
            started_at=now(),
        )
        db.session.add(rollback_dep)
        db.session.commit()

        try:
            patch_body = {
                "spec": {
                    "template": {
                        "spec": {
                            "containers": [
                                {"name": current["containers"][0]["name"], "image": current_image}
                            ]
                        }
                    }
                }
            }
            result = k8s.patch_deployment(dep_name, ns, patch_body)
            if not result.get("success"):
                raise DeploymentServiceError(f"Kubernetes patch failed: {result.get('error')}")

            rollback_dep.status = "success"
            dep.rollback_available = False
            rollback_dep.logs_json = json.dumps({
                "rollback_from": dep.deployment_id,
                "previous_status": dep.status,
                "image": current_image,
            })
            db.session.commit()
            logger.info(
                "Rollback deployment %s created from deployment %s by %s",
                rollback_dep.deployment_id, dep.deployment_id, triggered_by,
            )
        except Exception as e:
            rollback_dep.status = "failed"
            rollback_dep.logs_json = json.dumps({"error": str(e)})
            db.session.commit()
            raise DeploymentServiceError(f"Rollback failed: {e}")

        return DeploymentService._deployment_to_dict(rollback_dep)

    @staticmethod
    def get_rollout_status(deployment_id: int, project_id: int = None) -> dict:
        dep = Deployment.query.get_or_404(deployment_id)
        if project_id and dep.project_id != project_id:
            raise DeploymentServiceError("Deployment not found for this project")

        project = ConnectedProject.query.filter_by(id=dep.project_id).first()
        if not project:
            raise DeploymentServiceError("Project not found")

        ns = project.kubernetes_namespace
        dep_name = project.kubernetes_deployment
        if not ns or not dep_name:
            return {"status": "not_configured", "message": "No Kubernetes deployment configured for this project"}

        k8s = DeploymentService._get_k8s()
        return k8s.get_rollout_status(dep_name, ns)

    @staticmethod
    def update_status(deployment_id: str, status: str, workflow_run_id: int = None, logs: dict = None) -> dict:
        dep = Deployment.query.filter_by(deployment_id=deployment_id).first()
        if not dep:
            raise DeploymentServiceError("Deployment not found")

        if status not in DEPLOYMENT_STATUSES:
            raise DeploymentServiceError(f"Invalid status: {status}")

        dep.status = status
        if workflow_run_id is not None:
            dep.workflow_run_id = workflow_run_id
        if status in ("success", "failed", "rolled_back"):
            dep.completed_at = now()

        if logs:
            existing = json.loads(dep.logs_json or "{}")
            existing.update(logs)
            dep.logs_json = json.dumps(existing)

        if status == "success":
            dep.rollback_available = True

        db.session.commit()
        logger.info("Deployment %s status updated to %s", deployment_id, status)
        return DeploymentService._deployment_to_dict(dep)

    @staticmethod
    def _deployment_to_dict(d: Deployment) -> dict:
        return {
            "id": d.id,
            "deployment_id": d.deployment_id,
            "project_id": d.project_id,
            "repository": d.repository,
            "commit_sha": d.commit_sha,
            "branch": d.branch,
            "environment": d.environment,
            "status": d.status,
            "workflow_run_id": d.workflow_run_id,
            "started_at": to_iso(d.started_at),
            "completed_at": to_iso(d.completed_at),
            "triggered_by": d.triggered_by,
            "rollback_available": d.rollback_available,
            "logs_json": d.logs_json,
            "deployed_by": d.deployed_by,
            "created_at": to_iso(d.created_at),
        }
