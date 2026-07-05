from flask import Blueprint, jsonify, request
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
    error, result = AuthService.login(username, password)
    if error:
        return jsonify(error), 401
    return jsonify(result), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"msg": "Request body is required"}), 400
    name = data.get('name')
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    error, result = AuthService.register(name, email, username, password)
    if error:
        return jsonify(error), 400
    return jsonify(result), 201
