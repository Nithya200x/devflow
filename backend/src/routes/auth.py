from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Request body is required"}), 400
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"msg": "Username and password are required"}), 400
    result = AuthService.login(username, password)
    if result:
        return jsonify(result), 200
    return jsonify({"msg": "Bad username or password"}), 401
