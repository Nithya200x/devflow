import os
import logging
from datetime import timedelta

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
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", 'sqlite:///' + os.path.join(database_dir, 'app.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    TOKEN_ENCRYPTION_KEY = os.getenv("TOKEN_ENCRYPTION_KEY", "devflow-default-enc-key")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
    GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    JENKINS_URL = os.getenv("JENKINS_URL", "")
    JENKINS_USER = os.getenv("JENKINS_USER", "")
    JENKINS_TOKEN = os.getenv("JENKINS_TOKEN", "")
    DOCKER_HUB_USERNAME = os.getenv("DOCKER_HUB_USERNAME", "")
    DOCKER_HUB_TOKEN = os.getenv("DOCKER_HUB_TOKEN", "")
    KUBE_CONFIG_PATH = os.getenv("KUBE_CONFIG_PATH", "")
    PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "")
    GRAFANA_URL = os.getenv("GRAFANA_URL", "")
    GRAFANA_API_KEY = os.getenv("GRAFANA_API_KEY", "")
    JIRA_URL = os.getenv("JIRA_URL", "")
    JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
    JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
    SMTP_SERVER = os.getenv("SMTP_SERVER", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
