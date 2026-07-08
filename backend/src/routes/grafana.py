import logging
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from services.grafana_service import GrafanaService

logger = logging.getLogger(__name__)

grafana_bp = Blueprint("grafana", __name__)

_grafana = GrafanaService()


@grafana_bp.route("/health", methods=["GET"])
@jwt_required()
def health():
    status = _grafana.health_check()
    return jsonify(status), 200


@grafana_bp.route("/dashboards", methods=["GET"])
@jwt_required()
def list_dashboards():
    dashboards = _grafana.list_dashboards()
    return jsonify({"dashboards": dashboards, "count": len(dashboards)}), 200


@grafana_bp.route("/dashboards/<uid>", methods=["GET"])
@jwt_required()
def get_dashboard(uid):
    dashboard = _grafana.get_dashboard_references(uid)
    if not dashboard:
        return jsonify({"msg": "Dashboard not found"}), 404
    return jsonify(dashboard), 200


@grafana_bp.route("/dashboards/by-name/<name>", methods=["GET"])
@jwt_required()
def get_dashboard_by_name(name):
    dashboard = _grafana.find_dashboard_by_title(name)
    if not dashboard:
        return jsonify({"msg": "Dashboard not found"}), 404
    return jsonify(dashboard), 200


@grafana_bp.route("/datasources", methods=["GET"])
@jwt_required()
def list_datasources():
    datasources = _grafana.list_datasources()
    return jsonify({"datasources": datasources, "count": len(datasources)}), 200
