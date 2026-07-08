import os
import sys
import socket

DETECTED_ENV = None
DETECTED_RUNNING_IN = None


def detect_environment():
    global DETECTED_ENV, DETECTED_RUNNING_IN

    hostname = socket.gethostname()
    
    # Render detection
    if os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID"):
        DETECTED_ENV = "render"
        DETECTED_RUNNING_IN = "cloud"
        return "render"

    # Docker Compose detection (backwards compatibility)
    if os.getenv("DOCKER_COMPOSE_ENV") or os.getenv("COMPOSE_PROJECT_NAME"):
        DETECTED_ENV = "docker_compose"
        DETECTED_RUNNING_IN = "container"
        return "docker_compose"

    # Docker container detection
    if os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv"):
        DETECTED_ENV = "docker"
        DETECTED_RUNNING_IN = "container"
        return "docker"

    # Kubernetes detection
    if os.getenv("KUBERNETES_SERVICE_HOST") or os.getenv("KUBERNETES_PORT"):
        DETECTED_ENV = "kubernetes"
        DETECTED_RUNNING_IN = "container"
        return "kubernetes"

    # GitHub Codespaces
    if os.getenv("CODESPACES"):
        DETECTED_ENV = "codespaces"
        DETECTED_RUNNING_IN = "cloud"
        return "codespaces"

    # Default: local machine
    DETECTED_ENV = "local"
    DETECTED_RUNNING_IN = "local"
    return "local"


def get_environment():
    if DETECTED_ENV is None:
        detect_environment()
    return DETECTED_ENV


def get_running_in():
    if DETECTED_RUNNING_IN is None:
        detect_environment()
    return DETECTED_RUNNING_IN


def is_cloud():
    return get_running_in() == "cloud"


def is_container():
    return get_running_in() == "container"


def is_local():
    return get_running_in() == "local"


def get_environment_display():
    env = get_environment()
    mapping = {
        "render": "Render Cloud",
        "docker_compose": "Docker Compose",
        "docker": "Docker Container",
        "kubernetes": "Kubernetes",
        "codespaces": "GitHub Codespaces",
        "local": "Local Machine",
    }
    return mapping.get(env, env.capitalize())


STATUS_HEALTHY = "healthy"
STATUS_AVAILABLE_LOCALLY = "available_locally"
STATUS_CONNECTED = "connected"
STATUS_CONFIGURED = "configured"
STATUS_NOT_CONFIGURED = "not_configured"
STATUS_REMOTE_UNAVAILABLE = "remote_unavailable"
STATUS_AUTH_FAILED = "authentication_failed"
STATUS_CONNECTION_FAILED = "connection_failed"
STATUS_UNREACHABLE = "unreachable"
STATUS_REMOTE_ENV = "remote_environment"
STATUS_DISABLED = "disabled"

HEALTH_DISPLAY_NAMES = {
    "healthy": "Healthy",
    "available_locally": "Available Locally",
    "connected": "Connected",
    "configured": "Configured",
    "not_configured": "Not Configured",
    "remote_unavailable": "Remote Unavailable",
    "authentication_failed": "Authentication Failed",
    "connection_failed": "Connection Failed",
    "unreachable": "Unreachable",
    "remote_environment": "Remote Environment",
    "disabled": "Disabled",
}


def make_service_status(connected, service_name, is_local_service=False, error=None, status_override=None):
    env = get_environment()
    running_in = get_running_in()

    if status_override:
        return {
            "status": status_override,
            "detail": HEALTH_DISPLAY_NAMES.get(status_override, status_override),
            "environment": get_environment_display(),
        }

    if connected:
        return {
            "status": "healthy",
            "detail": "Connected and operational",
            "environment": get_environment_display(),
        }

    if error:
        err_str = str(error).lower()
        if "401" in err_str or "403" in err_str or "unauthorized" in err_str or "authentication" in err_str or "invalid key" in err_str or "invalid_api_key" in err_str:
            return {
                "status": "authentication_failed",
                "detail": f"Authentication failed: The API key or credentials are invalid.",
                "environment": get_environment_display(),
            }
        if "timeout" in err_str or "timed out" in err_str:
            return {
                "status": "unreachable",
                "detail": f"Connection timed out: The service is not responding.",
                "environment": get_environment_display(),
            }
        if "refused" in err_str or "111" in err_str or "connection refused" in err_str:
            if is_local_service:
                return {
                    "status": "available_locally",
                    "detail": f"{service_name} is running on the local development machine and cannot be accessed from this deployment.",
                    "environment": get_environment_display(),
                }
            return {
                "status": "connection_failed",
                "detail": f"Connection refused: The service is not running or not reachable.",
                "environment": get_environment_display(),
            }
        if "nodename nor servname provided" in err_str or "getaddrinfo" in err_str or "name resolution" in err_str:
            return {
                "status": "unreachable",
                "detail": f"DNS resolution failed: The service hostname could not be resolved.",
                "environment": get_environment_display(),
            }
        if "ssl" in err_str and ("eof" in err_str or "handshake" in err_str):
            return {
                "status": "connection_failed",
                "detail": f"SSL/TLS connection error: {error}",
                "environment": get_environment_display(),
            }
        if "429" in err_str or "quota" in err_str or "rate limit" in err_str:
            return {
                "status": "unreachable",
                "detail": f"API rate limit exceeded or quota reached.",
                "environment": get_environment_display(),
            }

    if is_local_service and running_in in ("cloud", "container"):
        return {
            "status": "available_locally",
            "detail": f"{service_name} is running on the local development machine and cannot be accessed from this deployment.",
            "environment": get_environment_display(),
        }

    env_var = f"{service_name.upper().replace(' ', '_')}_URL"
    if not os.getenv(env_var):
        return {
            "status": "not_configured",
            "detail": f"{env_var} environment variable is not set.",
            "environment": get_environment_display(),
        }

    return {
        "status": "connection_failed",
        "detail": "Could not connect to service. Check the configuration and ensure the service is running.",
        "environment": get_environment_display(),
    }


def is_status_healthy(status):
    return status in ("healthy", "connected", "configured")


def is_status_warning(status):
    return status in ("available_locally", "remote_environment", "remote_unavailable")


def is_status_error(status):
    return status in ("authentication_failed", "connection_failed", "unreachable", "disabled")


HEALTH_BADGE_COLORS = {
    "healthy": "#10b981",
    "connected": "#10b981",
    "configured": "#10b981",
    "available_locally": "#0ea5e9",
    "remote_environment": "#0ea5e9",
    "remote_unavailable": "#f59e0b",
    "not_configured": "#6b7280",
    "authentication_failed": "#ef4444",
    "connection_failed": "#ef4444",
    "unreachable": "#ef4444",
    "disabled": "#6b7280",
    "degraded": "#f59e0b",
    "unknown": "#9ca3af",
}


def standard_health_response(service_name, status, configured=True, reachable=False, message=None, details=None):
    env = get_environment_display()
    return {
        "service": service_name,
        "status": status,
        "configured": configured,
        "reachable": reachable,
        "environment": env,
        "message": message or HEALTH_DISPLAY_NAMES.get(status, status),
        "details": details or {},
    }
