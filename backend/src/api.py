from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User, Project, Cluster, Incident, Deployment
import datetime
import random

api_bp = Blueprint('api', __name__)

def check_and_update_deployments():
    """Auto-complete running deployments after 30 seconds and return True if any are currently running."""
    thirty_seconds_ago = datetime.datetime.utcnow() - datetime.timedelta(seconds=30)
    
    old_running = Deployment.query.filter(Deployment.status == "running", Deployment.created_at < thirty_seconds_ago).all()
    if old_running:
        for d in old_running:
            d.status = "success"
        db.session.commit()
        
    return Deployment.query.filter_by(status="running").count() > 0

@api_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        access_token = create_access_token(
            identity=user.username, 
            additional_claims={'role': user.role}
        )
        return jsonify(access_token=access_token, user={'username': user.username, 'role': user.role}), 200
    
    return jsonify({"msg": "Bad username or password"}), 401

@api_bp.route('/projects', methods=['GET'])
@jwt_required()
def get_projects():
    projects = Project.query.all()
    return jsonify([{
        "id": p.id, 
        "name": p.name, 
        "repository_url": p.repository_url,
        "description": p.description,
        "created_at": p.created_at.isoformat()
    } for p in projects]), 200

@api_bp.route('/deployments', methods=['GET', 'POST'])
@jwt_required()
def handle_deployments():
    if request.method == 'GET':
        check_and_update_deployments() # Update statuses when fetching
        deployments = Deployment.query.order_by(Deployment.created_at.desc()).all()
        return jsonify([{
            "id": d.id,
            "project_id": d.project_id,
            "environment": d.environment,
            "status": d.status,
            "deployed_by": d.deployed_by,
            "created_at": d.created_at.isoformat()
        } for d in deployments]), 200
    
    elif request.method == 'POST':
        data = request.get_json()
        current_username = get_jwt_identity()
        
        d = Deployment(
            project_id=data.get('project_id'),
            environment=data.get('environment', 'dev'),
            status="running",
            deployed_by=current_username
        )
        db.session.add(d)
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": f"Deployment triggered for project {d.project_id} to {d.environment}",
            "deployment_id": d.id
        }), 201

@api_bp.route('/deployments/<int:deployment_id>/rollback', methods=['POST'])
@jwt_required()
def rollback_deployment(deployment_id):
    d = Deployment.query.get_or_404(deployment_id)
    current_username = get_jwt_identity()
    
    rollback_dep = Deployment(
        project_id=d.project_id,
        environment=d.environment,
        status="running",
        deployed_by=current_username
    )
    db.session.add(rollback_dep)
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "message": f"Rollback triggered for project {d.project_id}",
        "deployment_id": rollback_dep.id
    }), 201

@api_bp.route('/clusters', methods=['GET'])
@jwt_required()
def get_clusters():
    is_deploying = check_and_update_deployments()
    clusters = Cluster.query.all()
    
    return jsonify([{
        "id": c.id,
        "name": c.name,
        "status": c.status,
        "node_count": c.node_count,
        # Spike CPU/Memory if a deployment is currently running
        "cpu_percent": random.randint(85, 98) if is_deploying else random.randint(30, 65),
        "mem_percent": random.randint(80, 95) if is_deploying else random.randint(40, 75),
        "pod_count": random.randint(15, 60)
    } for c in clusters]), 200

@api_bp.route('/clusters/<int:cluster_id>/logs', methods=['GET'])
@jwt_required()
def get_cluster_logs(cluster_id):
    is_deploying = check_and_update_deployments()
    
    if is_deploying:
        logs = [
            "[INFO] Triggered rolling update for deployment/devflow-app",
            "[INFO] Pulling new image registry.local/devflow-app:latest",
            "[INFO] Terminating old pod devflow-app-5d6f5c88b9-old",
            "[WARN] High CPU utilization during container startup",
            "[INFO] Running database migrations via init container",
            "[INFO] Liveness probe success for new pod devflow-app-5d6f5c88b9-new"
        ]
    else:
        logs = [
            "[INFO] Node worker-1 joined cluster",
            "[INFO] Pod devflow-api-7d6f5c88b9-x2j9k is Running",
            "[WARN] Memory threshold crossed on node worker-2",
            "[INFO] HTTP GET /health returned 200 OK",
            "[INFO] Garbage collection freed 120MB on heap",
            "[ERROR] Failed to connect to Redis cache (retry 1/3)",
            "[INFO] Received metric payload from prometheus-agent"
        ]
        
    return jsonify({"logs": random.sample(logs, k=random.randint(2, 5))}), 200

@api_bp.route('/incidents', methods=['GET', 'POST'])
@jwt_required()
def handle_incidents():
    if request.method == 'GET':
        incidents = Incident.query.order_by(Incident.created_at.desc()).all()
        return jsonify([{
            "id": i.id,
            "title": i.title,
            "status": i.status,
            "severity": i.severity,
            "created_at": i.created_at.isoformat()
        } for i in incidents]), 200
        
    elif request.method == 'POST':
        data = request.get_json()
        i = Incident(
            title=data.get('title'),
            severity=data.get('severity', 'medium')
        )
        db.session.add(i)
        db.session.commit()
        return jsonify({"message": "Incident created", "id": i.id}), 201

@api_bp.route('/incidents/<int:incident_id>', methods=['PATCH'])
@jwt_required()
def update_incident(incident_id):
    i = Incident.query.get_or_404(incident_id)
    data = request.get_json()
    if 'status' in data:
        i.status = data['status']
    db.session.commit()
    return jsonify({"message": "Incident updated"}), 200
