from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, GitRepository, ConnectedProject
from extensions import db, retry_on_db_disconnect
from services.github_auth import PATGitHubAuth
from services.github_service import GitHubService
from utils.encryption import encrypt_token, decrypt_token
from utils.time import to_iso
import logging

logger = logging.getLogger(__name__)

github_bp = Blueprint('github', __name__)


def _get_authenticated_service(username):
    user = User.query.filter_by(username=username).first()
    if not user or not user.github_token:
        return None, jsonify({"msg": "GitHub not connected. Connect your account first."}), 400
    token = decrypt_token(user.github_token)
    auth = PATGitHubAuth(token)
    return GitHubService(auth), None, None


def _github_repo_to_dict(r: dict) -> dict:
    return {
        "id": r["id"],
        "name": r["name"],
        "full_name": r["full_name"],
        "owner": r.get("owner", {}).get("login", ""),
        "description": r.get("description"),
        "html_url": r["html_url"],
        "clone_url": r.get("clone_url", ""),
        "default_branch": r.get("default_branch", "main"),
        "visibility": "private" if r.get("private") else "public",
        "language": r.get("language"),
        "stars": r.get("stargazers_count", 0),
        "forks": r.get("forks_count", 0),
        "topics": r.get("topics", []),
        "updated_at": r.get("updated_at"),
        "private": r.get("private", False)
    }


# ── Account Connection ──────────────────────────────────────────

@github_bp.route('/connect', methods=['POST'])
@jwt_required()
def connect():
    username = get_jwt_identity()
    data = request.get_json()
    if not data or not data.get('token'):
        return jsonify({"msg": "GitHub Personal Access Token is required"}), 400

    token = data['token'].strip()
    auth = PATGitHubAuth(token)
    gh = GitHubService(auth)
    try:
        gh_user = gh.get_user()
    except PermissionError as e:
        return jsonify({"msg": str(e)}), 401
    except Exception as e:
        logger.error(f"GitHub connection failed: {e}")
        return jsonify({"msg": "Failed to connect to GitHub. Check the token and try again."}), 502

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    user.github_token = encrypt_token(token)
    user.github_username = gh_user.get("login", "")
    db.session.commit()

    logger.info(f"User {username} connected GitHub account: {user.github_username}")
    return jsonify({
        "msg": "GitHub connected successfully",
        "github_username": user.github_username,
        "github_id": gh_user.get("id"),
        "github_avatar_url": gh_user.get("avatar_url")
    }), 200


@github_bp.route('/disconnect', methods=['DELETE'])
@jwt_required()
def disconnect():
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404
    user.github_token = ""
    user.github_username = ""
    db.session.commit()
    GitRepository.query.filter_by(connected_by=username).delete()
    db.session.commit()
    logger.info(f"User {username} disconnected GitHub account")
    return jsonify({"msg": "GitHub disconnected successfully"}), 200


@github_bp.route('/status', methods=['GET'])
@jwt_required()
def status():
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404
    return jsonify({
        "connected": bool(user.github_token and user.github_username),
        "github_username": user.github_username or ""
    }), 200


# ── GitHub API Proxy (live from GitHub) ─────────────────────────

@github_bp.route('/repos', methods=['GET'])
@jwt_required()
def list_github_repos():
    username = get_jwt_identity()
    gh, err, status = _get_authenticated_service(username)
    if err:
        return err, status
    try:
        data = gh.get_repos()
    except PermissionError as e:
        return jsonify({"msg": str(e)}), 401
    except Exception as e:
        logger.error(f"Failed to fetch repos: {e}")
        return jsonify({"msg": "Failed to fetch repositories from GitHub."}), 502
    return jsonify([_github_repo_to_dict(r) for r in data]), 200


@github_bp.route('/search', methods=['GET'])
@jwt_required()
def search_repos():
    username = get_jwt_identity()
    query = request.args.get("q", "")
    if not query:
        return jsonify({"msg": "Search query 'q' is required"}), 400
    gh, err, status = _get_authenticated_service(username)
    if err:
        return err, status
    try:
        data = gh._get("/search/repositories", params={"q": query, "per_page": 20})
    except Exception as e:
        logger.error(f"GitHub search failed: {e}")
        return jsonify({"msg": "Search failed."}), 502
    return jsonify([_github_repo_to_dict(r) for r in data.get("items", [])]), 200


# ── Connected Repositories (stored in DB) ───────────────────────

@github_bp.route('/repositories', methods=['GET'])
@jwt_required()
def list_connected():
    username = get_jwt_identity()
    repos = GitRepository.query.filter_by(connected_by=username).order_by(GitRepository.created_at.desc()).all()
    from models import ConnectedProject
    connected_projects = {
        cp.github_repo_id: cp.id
        for cp in ConnectedProject.query.filter_by(connected_by=username).all()
    }
    return jsonify([{
        "id": r.id,
        "repo_id": r.repo_id,
        "project_id": connected_projects.get(r.repo_id),
        "owner": r.owner,
        "name": r.name,
        "full_name": r.full_name,
        "description": r.description,
        "html_url": r.html_url,
        "clone_url": r.clone_url,
        "default_branch": r.default_branch,
        "visibility": r.visibility,
        "language": r.language,
        "stars": r.stars,
        "forks": r.forks,
        "topics": r.topics.split(",") if r.topics else [],
        "webhook_enabled": r.webhook_enabled,
        "created_at": to_iso(r.created_at)
    } for r in repos]), 200


@github_bp.route('/repositories', methods=['POST'])
@jwt_required()
def connect_repo():
    username = get_jwt_identity()
    data = request.get_json()
    if not data or not data.get('owner') or not data.get('name'):
        return jsonify({"msg": "owner and name are required"}), 400

    gh, err, status = _get_authenticated_service(username)
    if err:
        return err, status

    owner = data["owner"].strip()
    name = data["name"].strip()

    try:
        repo_data = gh.get_repo(owner, name)
    except FileNotFoundError:
        return jsonify({"msg": f"Repository {owner}/{name} not found."}), 404
    except PermissionError as e:
        return jsonify({"msg": str(e)}), 401
    except Exception as e:
        logger.error(f"Failed to connect repo: {e}")
        return jsonify({"msg": "Failed to fetch repository from GitHub."}), 502

    from models import ConnectedProject

    existing = GitRepository.query.filter_by(repo_id=repo_data["id"], connected_by=username).first()
    existing_project = ConnectedProject.query.filter_by(github_repo_id=repo_data["id"], connected_by=username).first()
    if existing and existing_project:
        return jsonify({"msg": "Repository already connected", "id": existing.id, "project_id": existing_project.id, "full_name": repo_data["full_name"]}), 200

    topics = []
    try:
        topics = gh.get_topics(owner, name)
    except Exception as e:
        logger.warning("Failed to fetch topics for %s/%s: %s", owner, name, e)

    repo = existing
    if not existing:
        repo = GitRepository(
            repo_id=repo_data["id"],
            owner=owner,
            name=name,
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
            connected_by=username
        )
        db.session.add(repo)

    project = existing_project
    if not existing_project:
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
        )
        db.session.add(project)

    db.session.commit()
    logger.info(f"User {username} connected repository {repo.full_name} with project mapping")

    # Auto-discover matching infrastructure
    try:
        _auto_discover_infrastructure(project)
    except Exception as e:
        logger.warning(f"Auto-discovery failed for {repo.full_name}: {e}")

    # Fetch and cache initial GitHub data for the project overview
    try:
        commits = gh.get_commits(owner, name, per_page=5)
        branches = gh.get_branches(owner, name)
        prs = gh.get_pull_requests(owner, name, state="all")
    except Exception as e:
        logger.warning(f"Failed to cache initial GH data for {repo.full_name}: {e}")

    return jsonify({
        "msg": "Repository connected successfully",
        "id": repo.id,
        "project_id": project.id,
        "full_name": repo.full_name
    }), 201


def _auto_discover_infrastructure(project):
    """Try to match the connected repo to existing Docker, Jenkins, K8s resources."""
    import fnmatch
    name_lower = project.name.lower()

    # Docker: look for containers whose name matches the repo name
    try:
        from services.docker_service import DockerService
        ds = DockerService()
        containers = ds.list_containers(all=True)
        if containers:
            for c in containers:
                for n in (c.get("Names") or []):
                    cname = n.lstrip("/").lower()
                    if name_lower in cname or fnmatch.fnmatch(cname, f"*{name_lower}*"):
                        project.docker_container = cname
                        project.docker_image = c.get("Image", "")
                        logger.info(f"Auto-discovered Docker container: {cname}")
                        break
                if project.docker_container:
                    break
    except Exception as e:
        logger.debug(f"Docker auto-discovery skipped: {e}")

    # Jenkins: try to find a job matching the repo name via API
    try:
        from config.config import Config
        if Config.JENKINS_URL and Config.JENKINS_USERNAME:
            import requests
            from requests.auth import HTTPBasicAuth
            api_token = Config.JENKINS_API_TOKEN or Config.JENKINS_TOKEN
            resp = requests.get(
                f"{Config.JENKINS_URL.rstrip('/')}/api/json?tree=jobs[name]",
                auth=HTTPBasicAuth(Config.JENKINS_USERNAME, api_token),
                timeout=10,
            )
            if resp.ok:
                data = resp.json()
                for job in data.get("jobs", []):
                    jname = job.get("name", "").lower()
                    if name_lower in jname or fnmatch.fnmatch(jname, f"*{name_lower}*"):
                        project.jenkins_job_name = job.get("name", "")
                        logger.info(f"Auto-discovered Jenkins job: {job.get('name', '')}")
                        break
    except Exception as e:
        logger.debug(f"Jenkins auto-discovery skipped: {e}")

    # Kubernetes: try to find deployments matching the repo name
    try:
        from services.kubernetes_service import KubernetesService
        ks = KubernetesService()
        namespaces = ks.list_namespaces()
        for ns in (namespaces or []):
            ns_name = ns.get("metadata", {}).get("name", "")
            if name_lower in ns_name.lower():
                deployments = ks.list_deployments(namespace=ns_name)
                for dep in (deployments or []):
                    dname = dep.get("metadata", {}).get("name", "")
                    if name_lower in dname.lower():
                        project.kubernetes_namespace = ns_name
                        project.kubernetes_deployment = dname
                        logger.info(f"Auto-discovered K8s: {ns_name}/{dname}")
                        break
                if project.kubernetes_namespace:
                    break
        if not project.kubernetes_namespace:
            # Try default namespace as fallback
            deployments = ks.list_deployments(namespace="default")
            for dep in (deployments or []):
                dname = dep.get("metadata", {}).get("name", "")
                if name_lower in dname.lower():
                    project.kubernetes_namespace = "default"
                    project.kubernetes_deployment = dname
                    logger.info(f"Auto-discovered K8s in default: {dname}")
                    break
    except Exception as e:
        logger.debug(f"K8s auto-discovery skipped: {e}")

    # Prometheus: set label selector if namespace known
    if project.kubernetes_namespace:
        project.prometheus_labels = f"namespace='{project.kubernetes_namespace}'"
    else:
        project.prometheus_labels = f"app='{project.name}'"

    # Grafana: try to find a dashboard matching the repo name
    try:
        from config.config import Config
        if Config.GRAFANA_URL:
            from services.grafana_service import GrafanaService
            gs = GrafanaService()
            dashboards = gs.list_dashboards()
            if dashboards:
                for d in dashboards:
                    dtitle = d.get("title", "").lower()
                    if name_lower in dtitle:
                        project.grafana_dashboard = d.get("title", "")
                        logger.info(f"Auto-discovered Grafana dashboard: {d.get('title', '')}")
                        break
    except Exception as e:
        logger.debug(f"Grafana auto-discovery skipped: {e}")

    db.session.commit()


@github_bp.route('/repositories/<int:repo_id>', methods=['DELETE'])
@jwt_required()
def disconnect_repo(repo_id):
    username = get_jwt_identity()
    repo = GitRepository.query.filter_by(id=repo_id, connected_by=username).first()
    if not repo:
        return jsonify({"msg": "Repository not found"}), 404
    connected_project = ConnectedProject.query.filter_by(
        github_repo_id=repo.repo_id, connected_by=username
    ).first()
    db.session.delete(repo)
    if connected_project:
        db.session.delete(connected_project)
    db.session.commit()
    logger.info(f"User {username} disconnected repository {repo.full_name}")
    remaining = GitRepository.query.filter_by(connected_by=username).all()
    return jsonify({
        "msg": "Repository disconnected",
        "repositories": [r.to_dict() for r in remaining],
    }), 200


# ── Repository Details ──────────────────────────────────────────

@github_bp.route('/repositories/<int:repo_id>/details', methods=['GET'])
@jwt_required()
def repo_details(repo_id):
    username = get_jwt_identity()
    repo = GitRepository.query.filter_by(id=repo_id, connected_by=username).first()
    if not repo:
        return jsonify({"msg": "Repository not found"}), 404

    gh, err, status = _get_authenticated_service(username)
    if err:
        return err, status

    try:
        stats = gh.get_repo_stats(repo.owner, repo.name)
    except Exception as e:
        logger.error(f"Failed to fetch repo details: {e}")
        return jsonify({"msg": "Failed to fetch repository details from GitHub."}), 502

    rd = stats["repo"]
    latest_release = {}
    try:
        latest_release = gh.get_latest_release(repo.owner, repo.name)
    except Exception as e:
        logger.warning("Failed to fetch latest release for %s/%s: %s", repo.owner, repo.name, e)

    return jsonify({
        "id": repo.id,
        "repo_id": repo.repo_id,
        "owner": repo.owner,
        "name": repo.name,
        "full_name": repo.full_name,
        "description": repo.description,
        "html_url": repo.html_url,
        "clone_url": repo.clone_url,
        "default_branch": repo.default_branch,
        "visibility": repo.visibility,
        "language": repo.language,
        "stars": repo.stars,
        "forks": repo.forks,
        "webhook_enabled": repo.webhook_enabled,
        "created_at": to_iso(repo.created_at),
        "topics_list": stats.get("topics", []),
        "languages": stats.get("languages", {}),
        "latest_release_tag": latest_release.get("tag_name", ""),
        "latest_release_url": latest_release.get("html_url", ""),
        "open_issues_count": rd.get("open_issues_count", 0),
        "watchers_count": rd.get("watchers_count", 0),
        "github_created_at": rd.get("created_at"),
        "github_updated_at": rd.get("updated_at"),
        "github_pushed_at": rd.get("pushed_at"),
        "size": rd.get("size", 0),
        "license": rd.get("license", {}).get("spdx_id", "") if rd.get("license") else "",
    }), 200


# ── Commits ─────────────────────────────────────────────────────

@github_bp.route('/repositories/<int:repo_id>/commits', methods=['GET'])
@jwt_required()
def repo_commits(repo_id):
    username = get_jwt_identity()
    repo = GitRepository.query.filter_by(id=repo_id, connected_by=username).first()
    if not repo:
        return jsonify({"msg": "Repository not found"}), 404

    gh, err, status = _get_authenticated_service(username)
    if err:
        return err, status

    branch = request.args.get("branch", repo.default_branch)
    try:
        data = gh.get_commits(repo.owner, repo.name, sha=branch)
    except Exception as e:
        logger.error(f"Failed to fetch commits: {e}")
        return jsonify({"msg": "Failed to fetch commits."}), 502

    return jsonify([{
        "sha": c["sha"],
        "message": c["commit"]["message"].split("\n")[0],
        "full_message": c["commit"]["message"],
        "author_name": c["commit"]["author"]["name"],
        "author_email": c["commit"]["author"]["email"],
        "author_login": c.get("author", {}).get("login", "") if c.get("author") else "",
        "author_avatar": c.get("author", {}).get("avatar_url", "") if c.get("author") else "",
        "date": c["commit"]["author"]["date"],
        "url": c["html_url"]
    } for c in data]), 200


# ── Branches ────────────────────────────────────────────────────

@github_bp.route('/repositories/<int:repo_id>/branches', methods=['GET'])
@jwt_required()
def repo_branches(repo_id):
    username = get_jwt_identity()
    repo = GitRepository.query.filter_by(id=repo_id, connected_by=username).first()
    if not repo:
        return jsonify({"msg": "Repository not found"}), 404

    gh, err, status = _get_authenticated_service(username)
    if err:
        return err, status

    try:
        data = gh.get_branches(repo.owner, repo.name)
    except Exception as e:
        logger.error(f"Failed to fetch branches: {e}")
        return jsonify({"msg": "Failed to fetch branches."}), 502

    result = []
    for b in data:
        branch_name = b["name"]
        protected = b.get("protected", False)
        last_commit_sha = b.get("commit", {}).get("sha", "")
        last_commit_url = b.get("commit", {}).get("url", "")
        result.append({
            "name": branch_name,
            "protected": protected,
            "last_commit_sha": last_commit_sha,
        })
    return jsonify(result), 200


# ── Pull Requests ───────────────────────────────────────────────

@github_bp.route('/repositories/<int:repo_id>/pulls', methods=['GET'])
@jwt_required()
def repo_pulls(repo_id):
    username = get_jwt_identity()
    repo = GitRepository.query.filter_by(id=repo_id, connected_by=username).first()
    if not repo:
        return jsonify({"msg": "Repository not found"}), 404

    gh, err, status = _get_authenticated_service(username)
    if err:
        return err, status

    state = request.args.get("state", "all")
    try:
        data = gh.get_pull_requests(repo.owner, repo.name, state=state)
    except Exception as e:
        logger.error(f"Failed to fetch PRs: {e}")
        return jsonify({"msg": "Failed to fetch pull requests."}), 502

    return jsonify([{
        "id": pr["id"],
        "number": pr["number"],
        "title": pr["title"],
        "body": pr.get("body", ""),
        "state": pr["state"],
        "merged": pr.get("merged", False),
        "author": pr["user"]["login"] if pr.get("user") else "",
        "author_avatar": pr["user"]["avatar_url"] if pr.get("user") else "",
        "created_at": pr["created_at"],
        "updated_at": pr["updated_at"],
        "merged_at": pr.get("merged_at"),
        "head_branch": pr["head"]["ref"] if pr.get("head") else "",
        "base_branch": pr["base"]["ref"] if pr.get("base") else "",
        "html_url": pr["html_url"]
    } for pr in data]), 200


# ── Contributors ────────────────────────────────────────────────

@github_bp.route('/repositories/<int:repo_id>/contributors', methods=['GET'])
@jwt_required()
def repo_contributors(repo_id):
    username = get_jwt_identity()
    repo = GitRepository.query.filter_by(id=repo_id, connected_by=username).first()
    if not repo:
        return jsonify({"msg": "Repository not found"}), 404

    gh, err, status = _get_authenticated_service(username)
    if err:
        return err, status

    try:
        data = gh.get_contributors(repo.owner, repo.name)
    except Exception as e:
        logger.error(f"Failed to fetch contributors: {e}")
        return jsonify({"msg": "Failed to fetch contributors."}), 502

    return jsonify([{
        "login": c["login"],
        "avatar_url": c["avatar_url"],
        "contributions": c["contributions"],
        "html_url": c["html_url"]
    } for c in data]), 200


# ── Dashboard Summary ───────────────────────────────────────────

@github_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@retry_on_db_disconnect()
def dashboard_summary():
    username = get_jwt_identity()
    gh, err, status = _get_authenticated_service(username)
    if err:
        return jsonify({"connected": False, "github_username": ""}), 200

    repos = GitRepository.query.filter_by(connected_by=username).all()
    connected_count = len(repos)
    latest_commit = None
    open_prs = 0

    if repos:
        try:
            repo = repos[0]
            commits = gh.get_commits(repo.owner, repo.name, per_page=1)
            if commits:
                c = commits[0]
                latest_commit = {
                    "repo": repo.full_name,
                    "message": c["commit"]["message"].split("\n")[0],
                    "author": c["commit"]["author"]["name"],
                    "date": c["commit"]["author"]["date"],
                    "sha": c["sha"][:7]
                }
            for r in repos:
                try:
                    prs = gh.get_pull_requests(r.owner, r.name, state="open")
                    open_prs += len(prs)
                except Exception as e:
                    logger.warning("Failed to get PR count for %s/%s: %s", r.owner, r.name, e)
        except Exception as e:
            logger.warning("Dashboard aggregate error: %s", e)

    return jsonify({
        "connected": True,
        "github_username": User.query.filter_by(username=username).first().github_username,
        "connected_repos": connected_count,
        "latest_commit": latest_commit,
        "open_prs": open_prs
    }), 200
