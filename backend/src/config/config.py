import os
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


def validate_environment():
    warnings = []
    if not os.getenv("JWT_SECRET_KEY"):
        warnings.append("JWT_SECRET_KEY not set — using insecure default (dev only)")
    if not os.getenv("TOKEN_ENCRYPTION_KEY"):
        warnings.append("TOKEN_ENCRYPTION_KEY not set — using insecure default (dev only)")
    for key in ("JWT_SECRET_KEY", "TOKEN_ENCRYPTION_KEY"):
        val = os.getenv(key, "")
        if val in ("devflow-super-secret-key-change-in-prod", "devflow-default-enc-key"):
            warnings.append(f"{key} is set to a known default — rotate for production")
    ai_provider = os.getenv("AI_PROVIDER", "")
    valid_providers = ("openai", "openai-compatible", "ollama", "lmstudio", "groq")
    if ai_provider and ai_provider not in valid_providers:
        warnings.append(f"AI_PROVIDER '{ai_provider}' is not recognised (use: {', '.join(valid_providers)})")

    ai_key_var = "GROQ_API_KEY" if ai_provider == "groq" else "OPENAI_API_KEY"
    ai_key_label = "Groq" if ai_provider == "groq" else "OpenAI"
    for var, label in [
        ("GITHUB_TOKEN", "GitHub"),
        ("JENKINS_URL", "Jenkins"),
        ("PROMETHEUS_URL", "Prometheus"),
        ("GRAFANA_URL", "Grafana"),
        ("GRAFANA_API_KEY", "Grafana API key"),
        ("KUBE_CONFIG_PATH", "Kubernetes config"),
        ("SLACK_WEBHOOK_URL", "Slack"),
        ("SMTP_SERVER", "SMTP"),
        (ai_key_var, ai_key_label if ai_provider in ("openai", "openai-compatible", "groq") else f"{ai_key_label} (not needed for current AI_PROVIDER)"),
        ("JIRA_URL", "Jira"),
    ]:
        if not os.getenv(var):
            warnings.append(f"{label} integration not configured (env var {var} not set)")
    for w in warnings:
        if "JWT_SECRET_KEY" in w or "TOKEN_ENCRYPTION_KEY" in w:
            logger.warning("Config: %s", w)
        else:
            logger.info("Config: %s", w)
    return warnings


class Config:
    APP_NAME = os.getenv("APP_NAME", "DevFlow SaaS")
    APP_VERSION = os.getenv("APP_VERSION", "2.0.0")
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    PORT = int(os.getenv("PORT", "5000"))

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "devflow-super-secret-key-change-in-prod")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_EXPIRY_HOURS", "24")))

    basedir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    database_dir = os.path.join(basedir, 'database')
    os.makedirs(database_dir, exist_ok=True)

    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = db_url if db_url else 'sqlite:///' + os.path.join(database_dir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    TOKEN_ENCRYPTION_KEY = os.getenv("TOKEN_ENCRYPTION_KEY", "devflow-default-enc-key")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
    GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    JENKINS_URL = os.getenv("JENKINS_URL", "")
    JENKINS_USER = os.getenv("JENKINS_USER", "")
    JENKINS_TOKEN = os.getenv("JENKINS_TOKEN", "")
    JENKINS_USERNAME = os.getenv("JENKINS_USERNAME", "")
    JENKINS_API_TOKEN = os.getenv("JENKINS_API_TOKEN", "")
    JENKINS_JOB_NAME = os.getenv("JENKINS_JOB_NAME", "devflow-pipeline")
    DOCKER_HUB_USERNAME = os.getenv("DOCKER_HUB_USERNAME", "")
    DOCKER_HUB_TOKEN = os.getenv("DOCKER_HUB_TOKEN", "")
    KUBE_CONFIG_PATH = os.getenv("KUBE_CONFIG_PATH", "")
    PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "")
    GRAFANA_URL = os.getenv("GRAFANA_URL", "")
    GRAFANA_API_KEY = os.getenv("GRAFANA_API_KEY", "")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "")
    JIRA_URL = os.getenv("JIRA_URL", "")
    JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
    JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
    SMTP_SERVER = os.getenv("SMTP_SERVER", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    ALERTMANAGER_URL = os.getenv("ALERTMANAGER_URL", "")
    AI_PROVIDER = os.getenv("AI_PROVIDER", "").lower()
    AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "60"))
    AI_MAX_CONCURRENT_REQUESTS = int(os.getenv("AI_MAX_CONCURRENT_REQUESTS", "3"))
    AI_RATE_LIMIT_BACKOFF = os.getenv("AI_RATE_LIMIT_BACKOFF", "true").lower() == "true"
    AI_ANALYSIS_CACHE = os.getenv("AI_ANALYSIS_CACHE", "true").lower() == "true"
