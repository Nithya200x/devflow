import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, ConnectedProject, GitRepository, Incident
from extensions import db
from services.connected_project_service import ConnectedProjectService
import json
import logging

from utils.time import to_iso

logger = logging.getLogger(__name__)

projects_bp = Blueprint('projects', __name__)


@projects_bp.route('', methods=['GET'])
@jwt_required()
def list_projects():
    username = get_jwt_identity()
    projects = ConnectedProject.query.filter_by(connected_by=username).order_by(ConnectedProject.connected_at.desc()).all()
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "github_owner": p.github_owner,
        "github_repo": p.github_repo,
        "full_name": p.full_name,
        "description": p.description,
        "html_url": p.html_url,
        "default_branch": p.default_branch,
        "language": p.language,
        "stars": p.stars,
        "forks": p.forks,
        "visibility": p.visibility,
        "status": p.status,
        "jenkins_job_name": p.jenkins_job_name,
        "docker_container": p.docker_container,
        "kubernetes_namespace": p.kubernetes_namespace,
        "kubernetes_deployment": p.kubernetes_deployment,
        "topics": p.topics.split(",") if p.topics else [],
        "connected_at": to_iso(p.connected_at),
    } for p in projects]), 200


@projects_bp.route('', methods=['POST'])
@jwt_required()
def connect_repo_to_project():
    username = get_jwt_identity()
    data = request.get_json()
    if not data or not data.get('owner') or not data.get('name'):
        return jsonify({"msg": "owner and name are required"}), 400

    from services.github_auth import PATGitHubAuth
    from services.github_service import GitHubService
    from utils.encryption import decrypt_token

    user = User.query.filter_by(username=username).first()
    if not user or not user.github_token:
        return jsonify({"msg": "GitHub not connected"}), 400
    token = decrypt_token(user.github_token)
    auth = PATGitHubAuth(token)
    gh = GitHubService(auth)

    owner = data["owner"].strip()
    name = data["name"].strip()

    try:
        repo_data = gh.get_repo(owner, name)
    except Exception as e:
        logger.error(f"Failed to fetch repo: {e}")
        return jsonify({"msg": "Failed to fetch repository from GitHub."}), 502

    existing = ConnectedProject.query.filter_by(github_repo_id=repo_data["id"], connected_by=username).first()
    if existing:
        return jsonify({"msg": "Repository already connected as project", "id": existing.id}), 200

    topics = []
    try:
        topics = gh.get_topics(owner, name)
    except Exception as e:
        logger.warning(f"Failed to fetch topics: {e}")

    project = ConnectedProject(
        name=name,
        github_owner=owner,
        github_repo=name,
        github_repo_id=repo_data["id"],
        full_name=repo_data["full_name"],
        description=repo_data.get("description", ""),
        html_url=repo_data["html_url"],
        clone_url=repo_data.get("clone_url", ""),
        default_branch=repo_data.get("default_branch", "main"),
        visibility="private" if repo_data.get("private") else "public",
        language=repo_data.get("language") or "",
        stars=repo_data.get("stargazers_count", 0),
        forks=repo_data.get("forks_count", 0),
        topics=",".join(topics),
        status="active",
        connected_by=username,
        jenkins_job_name=data.get("jenkins_job_name", ""),
        docker_container=data.get("docker_container", ""),
        docker_image=data.get("docker_image", ""),
        kubernetes_namespace=data.get("kubernetes_namespace", ""),
        kubernetes_deployment=data.get("kubernetes_deployment", ""),
        prometheus_labels=data.get("prometheus_labels", ""),
        grafana_dashboard=data.get("grafana_dashboard", ""),
    )
    db.session.add(project)
    db.session.commit()
    logger.info(f"User {username} connected project {project.full_name}")

    return jsonify({
        "msg": "Project connected successfully",
        "id": project.id,
        "full_name": project.full_name
    }), 201


@projects_bp.route('/<int:project_id>', methods=['DELETE'])
@jwt_required()
def disconnect_project(project_id):
    username = get_jwt_identity()
    project = ConnectedProject.query.filter_by(id=project_id, connected_by=username).first()
    if not project:
        return jsonify({"msg": "Project not found"}), 404
    db.session.delete(project)
    db.session.commit()
    return jsonify({"msg": "Project disconnected"}), 200


@projects_bp.route('/<int:project_id>/overview', methods=['GET'])
@jwt_required()
def project_overview(project_id):
    username = get_jwt_identity()
    project = ConnectedProject.query.filter_by(id=project_id, connected_by=username).first()
    if not project:
        return jsonify({"msg": "Project not found"}), 404

    from services.github_auth import PATGitHubAuth
    from services.github_service import GitHubService
    from services.docker_service import DockerService
    from services.kubernetes_service import KubernetesService
    from services.prometheus_service import prometheus_service
    from services.grafana_service import GrafanaService
    from services.alertmanager_service import AlertmanagerService
    from services.jenkins_service import JenkinsService
    from utils.encryption import decrypt_token
    from config.config import Config

    user = User.query.filter_by(username=username).first()
    overview = {"project": {"id": project.id, "name": project.name, "full_name": project.full_name, "owner": project.github_owner, "html_url": project.html_url, "default_branch": project.default_branch, "description": project.description, "language": project.language, "visibility": project.visibility, "topics": project.topics.split(",") if project.topics else []}}

    # GitHub
    now = datetime.datetime.utcnow().isoformat()
    overview["github"] = {"connected": True, "service_status": "not_configured", "configured": bool(user and user.github_token), "last_checked": now, "error_message": None, "stars": project.stars, "forks": project.forks, "default_branch": project.default_branch, "language": project.language}
    if user and user.github_token:
        try:
            token = decrypt_token(user.github_token)
            auth = PATGitHubAuth(token)
            gh = GitHubService(auth)
            try:
                commits = gh.get_commits(project.github_owner, project.github_repo, per_page=1)
                overview["github"].update({
                    "latest_commit": commits[0]["commit"]["message"].split("\n")[0] if commits else None,
                    "latest_commit_sha": commits[0]["sha"][:7] if commits else None,
                    "latest_commit_date": commits[0]["commit"]["author"]["date"] if commits else None,
                    "latest_commit_author": commits[0]["commit"]["author"]["name"] if commits else None,
                })
            except Exception as e:
                logger.warning(f"GitHub commits fetch error: {e}")
            try:
                branches = gh.get_branches(project.github_owner, project.github_repo)
                overview["github"]["branch_count"] = len(branches)
            except Exception as e:
                logger.warning(f"GitHub branches fetch error: {e}")
            try:
                prs = gh.get_pull_requests(project.github_owner, project.github_repo, state="all")
                overview["github"]["open_prs"] = len([pr for pr in prs if pr["state"] == "open"])
                overview["github"]["total_prs"] = len(prs)
            except Exception as e:
                logger.warning(f"GitHub PRs fetch error: {e}")
            try:
                repo_data = gh.get_repo_stats(project.github_owner, project.github_repo)
                overview["github"]["stars"] = repo_data.get("repo", {}).get("stargazers_count", project.stars)
                overview["github"]["forks"] = repo_data.get("repo", {}).get("forks_count", project.forks)
                overview["github"]["language"] = repo_data.get("repo", {}).get("language", project.language) or project.language
            except Exception as e:
                logger.warning(f"GitHub stats fetch error: {e}")
            overview["github"]["service_status"] = "connected"
        except Exception as e:
            logger.warning(f"GitHub overview error: {e}")
            overview["github"]["error_message"] = str(e)
            overview["github"]["service_status"] = "unavailable"
            overview["github"]["last_checked"] = datetime.datetime.utcnow().isoformat()
    else:
        overview["github"]["error_message"] = "GitHub token not configured"

    # Jenkins
    overview["jenkins"] = {"connected": bool(project.jenkins_job_name), "service_status": "not_configured", "configured": bool(project.jenkins_job_name), "last_checked": datetime.datetime.utcnow().isoformat(), "error_message": None}
    if project.jenkins_job_name:
        try:
            js = JenkinsService()
            health = js.health_check()
            history = js.get_build_history()
            overview["jenkins"].update({
                "healthy": health.get("status") == "ok" if isinstance(health, dict) else False,
                "job_name": project.jenkins_job_name,
                "build_history": history.get("builds", []) if isinstance(history, dict) else [],
                "last_build": history.get("builds", [None])[0] if isinstance(history, dict) and history.get("builds") else None,
                "service_status": "connected",
                "last_checked": datetime.datetime.utcnow().isoformat(),
            })
        except Exception as e:
            logger.warning(f"Jenkins overview error: {e}")
            overview["jenkins"]["error_message"] = str(e)
            overview["jenkins"]["service_status"] = "unavailable"
            overview["jenkins"]["last_checked"] = datetime.datetime.utcnow().isoformat()
    else:
        overview["jenkins"]["healthy"] = False

    # Docker
    overview["docker"] = {"connected": bool(project.docker_container), "service_status": "not_configured", "configured": bool(project.docker_container), "last_checked": datetime.datetime.utcnow().isoformat(), "error_message": None}
    if project.docker_container:
        try:
            ds = DockerService()
            containers = ds.list_containers(filters={"name": project.docker_container})
            matched = [c for c in containers if project.docker_container in c.get("Names", [""])[0] if c.get("Names")] if containers else []
            container = matched[0] if matched else None
            overview["docker"].update({
                "container_name": project.docker_container,
                "running": container["State"] == "running" if container else False,
                "status": container["Status"] if container else "not found",
                "image": container["Image"] if container else project.docker_image or "",
                "container_status": container.get("State", "not_found") if container else "not_found",
                "service_status": "connected",
                "last_checked": datetime.datetime.utcnow().isoformat(),
            })
            if container:
                try:
                    stats = ds.get_container_stats(container["Id"])
                    overview["docker"].update({
                        "cpu_percent": stats.get("cpu_percent", 0),
                        "memory_usage_mb": stats.get("memory_usage_mb", 0),
                        "memory_limit_mb": stats.get("memory_limit_mb", 0),
                        "memory_percent": stats.get("memory_percent", 0),
                    })
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Docker overview error: {e}")
            overview["docker"]["error_message"] = str(e)
            overview["docker"]["service_status"] = "unavailable"
            overview["docker"]["last_checked"] = datetime.datetime.utcnow().isoformat()
    else:
        overview["docker"]["running"] = False

    # Kubernetes
    overview["kubernetes"] = {"connected": bool(project.kubernetes_namespace and project.kubernetes_deployment), "service_status": "not_configured", "configured": bool(project.kubernetes_namespace and project.kubernetes_deployment), "last_checked": datetime.datetime.utcnow().isoformat(), "error_message": None}
    if project.kubernetes_namespace and project.kubernetes_deployment:
        try:
            ks = KubernetesService()
            deployment = ks.get_deployment(project.kubernetes_namespace, project.kubernetes_deployment)
            pods = ks.list_pods(namespace=project.kubernetes_namespace, label_selector=f"app={project.kubernetes_deployment}")
            overview["kubernetes"].update({
                "namespace": project.kubernetes_namespace,
                "deployment": project.kubernetes_deployment,
                "available_replicas": deployment.get("status", {}).get("availableReplicas", 0) if isinstance(deployment, dict) else 0,
                "desired_replicas": deployment.get("spec", {}).get("replicas", 0) if isinstance(deployment, dict) else 0,
                "pods": [{"name": p["metadata"]["name"], "status": p["status"]["phase"], "ready": all(c["ready"] for c in p["status"].get("containerStatuses", []))} for p in pods] if pods else [],
                "ready_pods": sum(1 for p in pods if all(c["ready"] for c in p["status"].get("containerStatuses", []))) if pods else 0,
                "total_pods": len(pods) if pods else 0,
                "service_status": "connected",
                "last_checked": datetime.datetime.utcnow().isoformat(),
            })
        except Exception as e:
            logger.warning(f"K8s overview error: {e}")
            overview["kubernetes"]["error_message"] = str(e)
            overview["kubernetes"]["service_status"] = "unavailable"
            overview["kubernetes"]["last_checked"] = datetime.datetime.utcnow().isoformat()
    else:
        overview["kubernetes"]["deployment"] = project.kubernetes_deployment or ""

    # Prometheus
    overview["prometheus"] = {"connected": bool(Config.PROMETHEUS_URL), "service_status": "not_configured", "configured": bool(Config.PROMETHEUS_URL), "last_checked": datetime.datetime.utcnow().isoformat(), "error_message": None, "has_kubernetes_metrics": False}
    if Config.PROMETHEUS_URL:
        try:
            ps = prometheus_service
            ps.connect()
            if ps.connected:
                overview["prometheus"]["service_status"] = "connected"
                overview["prometheus"]["last_checked"] = datetime.datetime.utcnow().isoformat()
                query_labels = project.prometheus_labels or ""
                overview["prometheus"].update({"labels": query_labels})
                up_result = ps.query("up")
                up_healthy = (
                    up_result.get("status") == "success"
                    and bool(up_result.get("data", {}).get("result"))
                )
                overview["prometheus"]["healthy"] = up_healthy
                if up_healthy:
                    ns_filter = f"{{namespace='{project.kubernetes_namespace}'}}" if project.kubernetes_namespace else ""
                    if ns_filter:
                        ns_up = ps.query(f'up{{namespace="{project.kubernetes_namespace}"}}')
                        has_k8s = bool(ns_up.get("data", {}).get("result"))
                        overview["prometheus"]["has_kubernetes_metrics"] = has_k8s
                        try:
                            overview["prometheus"]["cpu_usage"] = ps.query(f"avg(rate(container_cpu_usage_seconds_total{ns_filter}[5m])) * 100")
                        except Exception:
                            overview["prometheus"]["cpu_usage"] = None
                        try:
                            overview["prometheus"]["memory_usage"] = ps.query(f"avg(container_memory_working_set_bytes{ns_filter}) / 1024 / 1024")
                        except Exception:
                            overview["prometheus"]["memory_usage"] = None
                    else:
                        overview["prometheus"]["cpu_usage"] = None
                        overview["prometheus"]["memory_usage"] = None
                try:
                    alerts = ps.list_active_alerts()
                    overview["prometheus"]["active_alerts"] = len(alerts)
                except Exception:
                    overview["prometheus"]["active_alerts"] = 0
        except Exception as e:
            logger.warning(f"Prometheus overview error: {e}")
            overview["prometheus"]["error_message"] = str(e)
            overview["prometheus"]["healthy"] = False
            overview["prometheus"]["last_checked"] = datetime.datetime.utcnow().isoformat()
    else:
        overview["prometheus"]["healthy"] = False

    # Grafana
    overview["grafana"] = {"connected": bool(Config.GRAFANA_URL), "service_status": "not_configured", "configured": bool(Config.GRAFANA_URL), "last_checked": datetime.datetime.utcnow().isoformat(), "error_message": None}
    if Config.GRAFANA_URL:
        try:
            gs = GrafanaService()
            gs.connect()
            if gs.connected:
                dashboards = gs.list_dashboards()
                matched = None
                if project.grafana_dashboard:
                    matched = [d for d in (dashboards or []) if project.grafana_dashboard.lower() in d.get("title", "").lower() or project.grafana_dashboard.lower() in d.get("uid", "").lower()]
                overview["grafana"].update({
                    "dashboard_uid": matched[0]["uid"] if matched else None,
                    "dashboard_title": matched[0]["title"] if matched else project.grafana_dashboard or "",
                    "dashboard_url": f"{Config.GRAFANA_URL}/d/{matched[0]['uid']}" if matched else None,
                    "dashboards_count": len(dashboards or []),
                    "service_status": "connected",
                    "last_checked": datetime.datetime.utcnow().isoformat(),
                })
        except Exception as e:
            logger.warning(f"Grafana overview error: {e}")
            overview["grafana"]["error_message"] = str(e)
            overview["grafana"]["service_status"] = "unavailable"
            overview["grafana"]["last_checked"] = datetime.datetime.utcnow().isoformat()
    else:
        overview["grafana"]["dashboard_title"] = project.grafana_dashboard or ""

    # Alertmanager
    overview["alerts"] = {"active": 0, "resolved": 0}
    if Config.ALERTMANAGER_URL:
        try:
            am = AlertmanagerService(Config.ALERTMANAGER_URL)
            alerts_data = am.get_alerts()
            if isinstance(alerts_data, list):
                active = [a for a in alerts_data if a.get("status", {}).get("state") == "active"]
                overview["alerts"]["active"] = len(active)
                overview["alerts"]["resolved"] = len([a for a in alerts_data if a.get("status", {}).get("state") == "resolved"])
        except Exception as e:
            logger.warning(f"Alertmanager overview error: {e}")

    # Incidents (project-scoped — DB source of truth)
    overview["incidents"] = {"active": 0, "resolved": 0, "items": []}
    try:
        db_incidents = Incident.query.filter_by(project_id=project.id).order_by(Incident.created_at.desc()).all()
        overview["incidents"]["active"] = len([i for i in db_incidents if i.status == "open"])
        overview["incidents"]["resolved"] = len([i for i in db_incidents if i.status == "resolved"])
        overview["incidents"]["items"] = [
            {
                "incident_id": i.incident_id,
                "summary": i.title,
                "severity": i.severity,
                "status": i.status,
                "created_at": to_iso(i.created_at),
            }
            for i in db_incidents[:10]
        ]
    except Exception as e:
        logger.warning(f"Incidents overview error: {e}")

    # AI Analysis (scoped to this project's incidents)
    overview["ai_analysis"] = {"latest": None}
    try:
        from orchestration.models.event_store import AIAnalysisStore
        analysis = AIAnalysisStore.query.filter(
            AIAnalysisStore.project_id == project.id
        ).order_by(AIAnalysisStore.analyzed_at.desc()).first()
        if analysis:
            overview["ai_analysis"]["latest"] = {
                "incident_id": analysis.incident_id,
                "root_cause": analysis.root_cause or "",
                "confidence": analysis.confidence or 0,
                "summary": analysis.summary or "",
                "severity": analysis.severity or "",
                "suggested_fixes": json.loads(analysis.suggested_fixes_json) if analysis.suggested_fixes_json else [],
                "provider": analysis.provider or "",
                "model": analysis.model or "",
                "analyzed_at": to_iso(analysis.analyzed_at),
            }
    except Exception as e:
        logger.warning(f"AI analysis overview error: {e}")

    # Health calculation
    health = "healthy"
    issues = []
    if overview["incidents"]["active"] > 0:
        health = "warning"
        issues.append(f"{overview['incidents']['active']} active incident(s)")
    has_critical = any(i.get("severity") == "critical" for i in overview["incidents"]["items"])
    if has_critical:
        health = "critical"
        issues.append("Critical incident detected")
    if overview.get("jenkins", {}).get("last_build"):
        lb = overview["jenkins"]["last_build"]
        if isinstance(lb, dict) and lb.get("result") == "FAILURE":
            if health == "healthy":
                health = "warning"
            issues.append("Last build failed")
    if overview.get("docker", {}).get("container_status") == "running":
        pass
    elif project.docker_container and not overview["docker"].get("running"):
        if health == "healthy":
            health = "warning"
        issues.append("Docker container not running")
    if overview.get("kubernetes", {}).get("total_pods", 0) > 0:
        ready = overview["kubernetes"].get("ready_pods", 0)
        total = overview["kubernetes"].get("total_pods", 0)
        if ready < total:
            health = "warning"
            issues.append(f"{total - ready} pod(s) not ready")
    overview["health"] = {"status": health, "issues": issues}

    return jsonify(overview), 200


@projects_bp.route('/<int:project_id>/timeline', methods=['GET'])
@jwt_required()
def project_timeline(project_id):
    username = get_jwt_identity()
    project = ConnectedProject.query.filter_by(id=project_id, connected_by=username).first()
    if not project:
        return jsonify({"msg": "Project not found"}), 404

    events = []

    # GitHub events
    try:
        from services.github_auth import PATGitHubAuth
        from services.github_service import GitHubService
        from utils.encryption import decrypt_token
        user = User.query.filter_by(username=username).first()
        token = decrypt_token(user.github_token)
        auth = PATGitHubAuth(token)
        gh = GitHubService(auth)

        commits = gh.get_commits(project.github_owner, project.github_repo, per_page=5)
        for c in commits:
            events.append({
                "timestamp": c["commit"]["author"]["date"],
                "service": "GitHub",
                "event_type": "commit_pushed",
                "status": "success",
                "message": c["commit"]["message"].split("\n")[0],
                "metadata": {"sha": c["sha"][:7], "author": c["commit"]["author"]["name"]},
            })
        prs = gh.get_pull_requests(project.github_owner, project.github_repo, state="all")
        for pr in prs[:5]:
            events.append({
                "timestamp": pr["created_at"],
                "service": "GitHub",
                "event_type": "pull_request",
                "status": pr["state"],
                "message": f"PR #{pr['number']}: {pr['title']}",
                "metadata": {"number": pr["number"], "author": pr["user"]["login"] if pr.get("user") else ""},
            })
    except Exception as e:
        logger.warning(f"GitHub timeline error: {e}")

    # Jenkins events
    if project.jenkins_job_name:
        try:
            from config.config import Config
            from services.jenkins_service import JenkinsService
            js = JenkinsService(Config.JENKINS_URL, Config.JENKINS_USERNAME, Config.JENKINS_API_TOKEN, project.jenkins_job_name)
            history = js.get_build_history()
            for b in (history.get("builds", []) if isinstance(history, dict) else [])[:10]:
                events.append({
                    "timestamp": b.get("timestamp", ""),
                    "service": "Jenkins",
                    "event_type": "build",
                    "status": "success" if b.get("result") == "SUCCESS" else ("failed" if b.get("result") == "FAILURE" else "running"),
                    "message": f"Build #{b.get('number', '?')}: {b.get('result', 'PENDING')}",
                    "metadata": {"build_number": b.get("number", 0), "duration": b.get("duration", 0), "url": b.get("url", "")},
                })
        except Exception as e:
            logger.warning(f"Jenkins timeline error: {e}")

    # Docker events
    if project.docker_container:
        try:
            from services.docker_service import DockerService
            ds = DockerService()
            containers = ds.list_containers(all=True, filters={"name": project.docker_container})
            matched = [c for c in containers if c.get("Names") and any(project.docker_container in n for n in c["Names"])] if containers else []
            if matched:
                c = matched[0]
                status = c.get("Status", "unknown")
                events.append({
                    "timestamp": c.get("Created", ""),
                    "service": "Docker",
                    "event_type": "container",
                    "status": "running" if c.get("State") == "running" else ("exited" if c.get("State") == "exited" else status),
                    "message": f"Container {c.get('Names', [''])[0]}: {status}",
                    "metadata": {"container_id": c.get("Id", "")[:12], "image": c.get("Image", ""), "state": c.get("State", "")},
                })
        except Exception as e:
            logger.warning(f"Docker timeline error: {e}")

    # Kubernetes events
    if project.kubernetes_namespace and project.kubernetes_deployment:
        try:
            from services.kubernetes_service import KubernetesService
            ks = KubernetesService()
            k8s_events = ks.list_events(namespace=project.kubernetes_namespace)
            for e in (k8s_events or [])[:10]:
                events.append({
                    "timestamp": e.get("metadata", {}).get("creationTimestamp", ""),
                    "service": "Kubernetes",
                    "event_type": "kubernetes_event",
                    "status": e.get("type", "Normal").lower(),
                    "message": f"{e.get('reason', '')}: {e.get('message', '')[:100]}",
                    "metadata": {"involved_object": e.get("involvedObject", {}).get("name", ""), "reason": e.get("reason", "")},
                })
        except Exception as e:
            logger.warning(f"K8s timeline error: {e}")

    # Orchestration incidents (from DB, project-scoped)
    try:
        from orchestration.services.orchestration_service import get_orchestrator
        orch = get_orchestrator()
        orch_incidents = orch.get_all_incidents()
        project_incidents = [
            i for i in orch_incidents
            if getattr(i, "project_id", None) == project.id
            or project.full_name.lower() in i.repository.lower()
        ]
        for inc in project_incidents:
            events.append({
                "timestamp": to_iso(inc.created_at) or "",
                "service": "Orchestration",
                "event_type": "incident",
                "status": inc.severity if inc.status == "open" else "resolved",
                "message": f"Incident {inc.incident_id}: {inc.summary}",
                "metadata": {"incident_id": inc.incident_id, "severity": inc.severity, "status": inc.status},
            })
            if inc.ai_analysis:
                events.append({
                    "timestamp": to_iso(inc.created_at) or "",
                    "service": "AI Analysis",
                    "event_type": "ai_analysis",
                    "status": "completed",
                    "message": f"AI root cause: {inc.root_cause or 'N/A'} (confidence: {inc.confidence_score}%)",
                    "metadata": {"incident_id": inc.incident_id, "root_cause": inc.root_cause or "", "confidence": inc.confidence_score},
                })
            for t in inc.timeline:
                events.append({
                    "timestamp": to_iso(t.timestamp) or "",
                    "service": t.source.capitalize() if t.source else "System",
                    "event_type": t.event_type,
                    "status": "info",
                    "message": t.description,
                    "metadata": t.metadata,
                })
    except Exception as e:
        logger.warning(f"Orchestration timeline error: {e}")

    # Sort by timestamp descending
    events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)

    return jsonify({"events": events[:100], "total": len(events)}), 200


@projects_bp.route('/<int:project_id>/health', methods=['GET'])
@jwt_required()
def project_health(project_id):
    username = get_jwt_identity()
    project = ConnectedProject.query.filter_by(id=project_id, connected_by=username).first()
    if not project:
        return jsonify({"msg": "Project not found"}), 404

    checks = {
        "github": {"status": "healthy", "message": "Connected"},
        "jenkins": {"status": "disconnected", "message": "No Jenkins job configured"},
        "docker": {"status": "disconnected", "message": "No Docker container configured"},
        "kubernetes": {"status": "disconnected", "message": "No Kubernetes deployment configured"},
        "prometheus": {"status": "disconnected", "message": "Prometheus not configured"},
        "grafana": {"status": "disconnected", "message": "No Grafana dashboard configured"},
    }

    if project.jenkins_job_name:
        from config.config import Config
        try:
            from services.jenkins_service import JenkinsService
            js = JenkinsService()
            h = js.health_check()
            checks["jenkins"] = {"status": "healthy" if h.get("status") == "ok" else "unhealthy", "message": "Jenkins reachable" if h.get("status") == "ok" else "Jenkins unreachable"}
        except Exception:
            checks["jenkins"] = {"status": "unhealthy", "message": "Failed to connect to Jenkins"}

    if project.docker_container:
        try:
            from services.docker_service import DockerService
            ds = DockerService()
            containers = ds.list_containers(filters={"name": project.docker_container})
            matched = [c for c in containers if c.get("Names") and any(project.docker_container in n for n in c["Names"])] if containers else []
            if matched:
                running = matched[0].get("State") == "running"
                checks["docker"] = {"status": "healthy" if running else "warning", "message": f"Container {'running' if running else 'stopped'}"}
            else:
                checks["docker"] = {"status": "unhealthy", "message": "Container not found"}
        except Exception:
            checks["docker"] = {"status": "unhealthy", "message": "Failed to connect to Docker"}

    if project.kubernetes_namespace and project.kubernetes_deployment:
        try:
            from services.kubernetes_service import KubernetesService
            ks = KubernetesService()
            dep = ks.get_deployment(project.kubernetes_namespace, project.kubernetes_deployment)
            available = dep.get("status", {}).get("availableReplicas", 0) if isinstance(dep, dict) else 0
            desired = dep.get("spec", {}).get("replicas", 1) if isinstance(dep, dict) else 1
            checks["kubernetes"] = {"status": "healthy" if available == desired else ("warning" if available > 0 else "unhealthy"), "message": f"{available}/{desired} pods ready"}
        except Exception:
            checks["kubernetes"] = {"status": "unhealthy", "message": "Failed to connect to Kubernetes"}

    from config.config import Config
    if Config.PROMETHEUS_URL:
        try:
            from services.prometheus_service import prometheus_service
            ps = prometheus_service
            if hasattr(ps, 'connect'):
                ps.connect()
            h = ps.query("up")
            checks["prometheus"] = {"status": "healthy", "message": "Prometheus reachable"}
        except Exception:
            checks["prometheus"] = {"status": "unhealthy", "message": "Prometheus unreachable"}

    if Config.GRAFANA_URL:
        checks["grafana"] = {"status": "healthy", "message": "Grafana configured"}
        if project.grafana_dashboard:
            checks["grafana"]["dashboard"] = project.grafana_dashboard

    overall = "healthy"
    for k, v in checks.items():
        if v["status"] == "unhealthy":
            overall = "unhealthy"
            break
        if v["status"] == "warning":
            overall = "warning"

    return jsonify({"overall": overall, "checks": checks}), 200


@projects_bp.route('/<int:project_id>/deploy', methods=['POST'])
@jwt_required()
def project_deploy(project_id):
    username = get_jwt_identity()
    project = ConnectedProject.query.filter_by(id=project_id, connected_by=username).first()
    if not project:
        return jsonify({"msg": "Project not found"}), 404
    if not project.jenkins_job_name:
        return jsonify({"msg": "No Jenkins job configured for this project"}), 400

    from config.config import Config
    from services.jenkins_service import JenkinsService
    from services.github_auth import PATGitHubAuth
    from services.github_service import GitHubService
    from utils.encryption import decrypt_token

    user = User.query.filter_by(username=username).first()
    if user and user.github_token:
        try:
            token = decrypt_token(user.github_token)
            auth = PATGitHubAuth(token)
            gh = GitHubService(auth)
            commits = gh.get_commits(project.github_owner, project.github_repo, per_page=1)
            latest_sha = commits[0]["sha"][:7] if commits else ""
        except Exception:
            latest_sha = ""
    else:
        latest_sha = ""

    js = JenkinsService(Config.JENKINS_URL, Config.JENKINS_USERNAME, Config.JENKINS_API_TOKEN, project.jenkins_job_name)
    try:
        result = js.trigger_build(parameters={
            "REPOSITORY": project.full_name,
            "BRANCH": project.default_branch,
            "COMMIT_SHA": latest_sha,
            "TRIGGERED_BY": username,
        })
        return jsonify({"msg": "Build triggered", "data": result if isinstance(result, dict) else {}}), 200
    except Exception as e:
        return jsonify({"msg": f"Failed to trigger build: {str(e)}"}), 502
