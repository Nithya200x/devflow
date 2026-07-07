from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from services.cluster_service import ClusterService

clusters_bp = Blueprint('clusters', __name__)

@clusters_bp.route('', methods=['GET'])
@jwt_required()
def get_clusters():
    clusters = ClusterService.get_all_with_metrics()
    return jsonify(clusters), 200

@clusters_bp.route('/<int:cluster_id>/logs', methods=['GET'])
@jwt_required()
def get_cluster_logs(cluster_id):
    result = ClusterService.get_logs(cluster_id)
    return jsonify(result), 200
