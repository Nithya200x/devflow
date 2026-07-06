import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

from flask import Flask
from flask_cors import CORS
from config.config import Config, validate_environment
from extensions import db, migrate, jwt
from routes.auth import auth_bp
from routes.projects import projects_bp
from routes.deployments import deployments_bp
from routes.clusters import clusters_bp
from routes.incidents import incidents_bp
from routes.github import github_bp
from routes.jenkins import jenkins_bp
from routes.docker import docker_bp
from routes.kubernetes import kubernetes_bp
from routes.orchestration import orchestration_bp
from routes.prometheus import prometheus_bp
from routes.grafana import grafana_bp
from routes.alertmanager import alertmanager_bp
from routes.health import register_health_routes
from utils.seed import seed_data
from utils.logging import setup_logging
from orchestration.collectors.github_collector import GitHubEvidenceCollector
from orchestration.collectors.jenkins_collector import JenkinsEvidenceCollector
from orchestration.collectors.docker_collector import DockerEvidenceCollector
from orchestration.collectors.kubernetes_collector import KubernetesEvidenceCollector
from orchestration.collectors.prometheus_collector import PrometheusEvidenceCollector
from orchestration.collectors.grafana_collector import GrafanaEvidenceCollector

logger = setup_logging()


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
    validate_environment()
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = Config.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = Config.SQLALCHEMY_ENGINE_OPTIONS
    app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = Config.JWT_ACCESS_TOKEN_EXPIRES
    app.config['AI_PROVIDER'] = Config.AI_PROVIDER
    app.config['OPENAI_API_KEY'] = Config.OPENAI_API_KEY
    app.config['OPENAI_API_BASE'] = Config.OPENAI_API_BASE
    app.config['OPENAI_MODEL'] = Config.OPENAI_MODEL
    app.config['OLLAMA_URL'] = Config.OLLAMA_URL
    app.config['OLLAMA_MODEL'] = Config.OLLAMA_MODEL
    app.config['GROQ_API_KEY'] = Config.GROQ_API_KEY
    app.config['GROQ_MODEL'] = Config.GROQ_MODEL
    app.config['AI_TIMEOUT'] = Config.AI_TIMEOUT
    app.config['AI_MAX_CONCURRENT_REQUESTS'] = Config.AI_MAX_CONCURRENT_REQUESTS
    app.config['AI_RATE_LIMIT_BACKOFF'] = Config.AI_RATE_LIMIT_BACKOFF
    app.config['AI_ANALYSIS_CACHE'] = Config.AI_ANALYSIS_CACHE

    frontend_url = Config.FRONTEND_URL
    if frontend_url:
        CORS(app, resources={r"/api/*": {"origins": frontend_url}}, supports_credentials=True)
        logger.info("CORS restricted to frontend URL: %s", frontend_url)
    else:
        CORS(app)
        logger.info("CORS: no FRONTEND_URL set — allowing all origins (dev mode)")

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
    app.register_blueprint(jenkins_bp, url_prefix='/api/v1/jenkins')
    app.register_blueprint(docker_bp, url_prefix='/api/v1/docker')
    app.register_blueprint(kubernetes_bp, url_prefix='/api/v1/kubernetes')
    app.register_blueprint(prometheus_bp, url_prefix='/api/v1/prometheus')
    app.register_blueprint(grafana_bp, url_prefix='/api/v1/grafana')
    app.register_blueprint(alertmanager_bp, url_prefix='/api/v1/alertmanager')

    _init_orchestration(app)

    register_health_routes(app)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    with app.app_context():
        try:
            logger.info("Checking database schema...")
            db.create_all()
            db.session.commit()
            logger.info("Database schema ready")
        except Exception as e:
            db.session.rollback()
            logger.warning("Database schema initialization failed: %s", e)

        try:
            import models
            seed_data()
        except Exception as e:
            db.session.rollback()
            logger.warning("Seed data skipped: %s", e)

        try:
            from models import User
            if User.query.count() == 0:
                admin_username = os.getenv("ADMIN_USERNAME", "")
                admin_email = os.getenv("ADMIN_EMAIL", "")
                admin_password = os.getenv("ADMIN_PASSWORD", "")
                if admin_username and admin_email and admin_password:
                    admin = User(
                        name="Admin",
                        email=admin_email,
                        username=admin_username,
                        role="admin"
                    )
                    admin.set_password(admin_password)
                    db.session.add(admin)
                    db.session.commit()
                    logger.info("Initial admin user created")
        except Exception as e:
            db.session.rollback()
            logger.warning("Admin bootstrap skipped: %s", e)

        try:
            from orchestration.ai.service import AIService
            ai = AIService()
            provider = ai._get_provider()
            if provider:
                logger.info("AI service initialized: provider=%s model=%s", provider.name(), provider.model_name())
            else:
                logger.warning("AI service initialized but no provider configured")
        except Exception as e:
            logger.warning("AI service init skipped: %s", e)

    logger.info(f"{Config.APP_NAME} v{Config.APP_VERSION} started")
    return app

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.FLASK_DEBUG,
    )

