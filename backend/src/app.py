import os
from flask import Flask
from flask_cors import CORS
from config.config import Config
from extensions import db, migrate, jwt
from routes.auth import auth_bp
from routes.projects import projects_bp
from routes.deployments import deployments_bp
from routes.clusters import clusters_bp
from routes.incidents import incidents_bp
from routes.github import github_bp
from routes.orchestration import orchestration_bp
from routes.health import register_health_routes
from utils.seed import seed_data
from utils.logging import setup_logging
from orchestration import OrchestrationService
from orchestration.collectors.github_collector import GitHubEvidenceCollector
from orchestration.collectors.jenkins_collector import JenkinsEvidenceCollector
from orchestration.collectors.docker_collector import DockerEvidenceCollector
from orchestration.collectors.kubernetes_collector import KubernetesEvidenceCollector
from orchestration.collectors.prometheus_collector import PrometheusEvidenceCollector
from orchestration.collectors.grafana_collector import GrafanaEvidenceCollector

logger = setup_logging()

orchestration_service = OrchestrationService()


def _init_orchestration(app):
    try:
        from routes.orchestration import _service as os_service

        os_service.collector_registry.register("github", GitHubEvidenceCollector())
        os_service.collector_registry.register("jenkins", JenkinsEvidenceCollector())
        os_service.collector_registry.register("docker", DockerEvidenceCollector())
        os_service.collector_registry.register(
            "kubernetes", KubernetesEvidenceCollector()
        )
        os_service.collector_registry.register(
            "prometheus", PrometheusEvidenceCollector()
        )
        os_service.collector_registry.register("grafana", GrafanaEvidenceCollector())

        logger.info(
            f"Orchestration engine initialized with "
            f"{len(os_service.collector_registry.list_collectors())} collectors"
        )
    except Exception as e:
        logger.warning(f"Orchestration init skipped: {e}")


def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = Config.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = Config.JWT_ACCESS_TOKEN_EXPIRES

    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(projects_bp, url_prefix='/api/v1/projects')
    app.register_blueprint(deployments_bp, url_prefix='/api/v1/deployments')
    app.register_blueprint(clusters_bp, url_prefix='/api/v1/clusters')
    app.register_blueprint(incidents_bp, url_prefix='/api/v1/incidents')
    app.register_blueprint(github_bp, url_prefix='/api/v1/github')
    app.register_blueprint(orchestration_bp, url_prefix='/api/v1/orchestration')

    _init_orchestration(app)

    register_health_routes(app)

    with app.app_context():
        try:
            import models
            seed_data()
        except Exception as e:
            logger.warning(f"Seed data skipped: {e}")

    logger.info(f"{Config.APP_NAME} v{Config.APP_VERSION} started")
    return app

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.FLASK_DEBUG,
    )
