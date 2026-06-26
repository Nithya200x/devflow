import datetime
from extensions import db
from models import Deployment
import logging

logger = logging.getLogger(__name__)

class DeploymentService:

    @staticmethod
    def check_and_update():
        thirty_seconds_ago = datetime.datetime.utcnow() - datetime.timedelta(seconds=30)
        old_running = Deployment.query.filter(
            Deployment.status == "running",
            Deployment.created_at < thirty_seconds_ago
        ).all()
        if old_running:
            for d in old_running:
                d.status = "success"
                logger.info(f"Deployment {d.id} auto-completed to success")
            db.session.commit()
        return Deployment.query.filter_by(status="running").count() > 0

    @staticmethod
    def get_all():
        DeploymentService.check_and_update()
        return Deployment.query.order_by(Deployment.created_at.desc()).all()

    @staticmethod
    def create(project_id, environment, deployed_by):
        d = Deployment(
            project_id=project_id,
            environment=environment,
            status="running",
            deployed_by=deployed_by
        )
        db.session.add(d)
        db.session.commit()
        logger.info(f"Deployment created: project={project_id}, env={environment}, by={deployed_by}")
        return d

    @staticmethod
    def rollback(deployment_id, deployed_by):
        d = Deployment.query.get_or_404(deployment_id)
        rollback_dep = Deployment(
            project_id=d.project_id,
            environment=d.environment,
            status="running",
            deployed_by=deployed_by
        )
        db.session.add(rollback_dep)
        db.session.commit()
        logger.info(f"Rollback triggered for deployment {deployment_id} by {deployed_by}")
        return rollback_dep
