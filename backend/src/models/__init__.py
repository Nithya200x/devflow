from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from utils.time import now

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, default="")
    email = db.Column(db.String(120), unique=True, nullable=False, default="")
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="developer")
    github_token = db.Column(db.Text, default="")
    github_username = db.Column(db.String(80), default="")
    created_at = db.Column(db.DateTime(timezone=True), default=now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Project(db.Model):
    __tablename__ = 'project'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    repository_url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True), default=now)

class Cluster(db.Model):
    __tablename__ = 'cluster'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(50), default="active")
    node_count = db.Column(db.Integer, default=3)
    created_at = db.Column(db.DateTime(timezone=True), default=now)

class Deployment(db.Model):
    __tablename__ = 'deployment'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    environment = db.Column(db.String(20), default="dev")
    status = db.Column(db.String(20), default="running")
    deployed_by = db.Column(db.String(50))
    created_at = db.Column(db.DateTime(timezone=True), default=now)

class Incident(db.Model):
    __tablename__ = 'incident'
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.String(50), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, default="")
    status = db.Column(db.String(50), default="open")
    severity = db.Column(db.String(20), default="medium")
    source = db.Column(db.String(100), default="")
    project_id = db.Column(db.Integer, db.ForeignKey('connected_project.id'), nullable=True)
    evidence_json = db.Column(db.Text, default="[]")
    timeline_json = db.Column(db.Text, default="[]")
    ai_analysis_id = db.Column(db.Integer, db.ForeignKey('ai_analysis.id'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now)
    resolved_at = db.Column(db.DateTime, nullable=True)


class ConnectedProject(db.Model):
    __tablename__ = 'connected_project'
    id = db.Column(db.Integer, primary_key=True)
    # GitHub repo info
    name = db.Column(db.String(100), nullable=False)
    github_owner = db.Column(db.String(100), nullable=False)
    github_repo = db.Column(db.String(100), nullable=False)
    github_repo_id = db.Column(db.BigInteger, nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    html_url = db.Column(db.String(255), default="")
    clone_url = db.Column(db.String(255), default="")
    default_branch = db.Column(db.String(50), default="main")
    visibility = db.Column(db.String(20), default="public")
    language = db.Column(db.String(50), default="")
    stars = db.Column(db.Integer, default=0)
    forks = db.Column(db.Integer, default=0)
    topics = db.Column(db.Text, default="")
    # DevOps mapping fields
    jenkins_job_name = db.Column(db.String(100), default="")
    docker_container = db.Column(db.String(100), default="")
    docker_image = db.Column(db.String(200), default="")
    kubernetes_namespace = db.Column(db.String(100), default="")
    kubernetes_deployment = db.Column(db.String(100), default="")
    prometheus_labels = db.Column(db.Text, default="")
    grafana_dashboard = db.Column(db.String(200), default="")
    # Status
    status = db.Column(db.String(20), default="active")
    connected_by = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False)
    connected_at = db.Column(db.DateTime(timezone=True), default=now)


class GitRepository(db.Model):
    __tablename__ = 'git_repository'
    id = db.Column(db.Integer, primary_key=True)
    repo_id = db.Column(db.BigInteger, nullable=False)
    owner = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    html_url = db.Column(db.String(255), nullable=False)
    clone_url = db.Column(db.String(255), default="")
    default_branch = db.Column(db.String(50), default="main")
    visibility = db.Column(db.String(20), default="public")
    language = db.Column(db.String(50), default="")
    stars = db.Column(db.Integer, default=0)
    forks = db.Column(db.Integer, default=0)
    topics = db.Column(db.Text, default="")
    webhook_enabled = db.Column(db.Boolean, default=False)
    connected_by = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now)
