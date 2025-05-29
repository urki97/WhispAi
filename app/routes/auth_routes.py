from flask import request, jsonify
from app.routes import api
from app import db
from app.utils.jwt_utils import generate_jwt, generate_refresh_token, decode_jwt, jwt_required

@api.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email y contraseña requeridos"}), 400

    user = db.get_user_by_email(data["email"])
    if not user or not db.verify_password(user["password_hash"], data["password"]):
        return jsonify({"error": "Credenciales inválidas"}), 401

    access_token = generate_jwt(user["_id"], user.get("name"))
    refresh_token = generate_refresh_token(user["_id"])

    return jsonify({
        "user_id": user["_id"],
        "access_token": access_token,
        "refresh_token": refresh_token,
        "name": user.get("name")
    }), 200

@api.route('/api/refresh', methods=['POST'])
def refresh_token():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Refresh token no proporcionado"}), 401

    token = auth_header.split(" ")[1]

    try:
        payload = decode_jwt(token, refresh=True)
    except ValueError as e:
        return jsonify({"error": str(e)}), 401

    user = db.get_user_by_id(payload["sub"])
    if not user:
        return jsonify({"error": "Usuario no válido"}), 403

    new_access_token = generate_jwt(user["_id"], user.get("name"))
    return jsonify({"access_token": new_access_token}), 200

@api.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json()
    try:
        user = db.create_user(
            name=data.get("name"),
            email=data.get("email"),
            password=data.get("password")
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    access_token = generate_jwt(user["_id"], user.get("name"))
    refresh_token = generate_refresh_token(user["_id"])

    return jsonify({
        "user_id": user["_id"],
        "access_token": access_token,
        "refresh_token": refresh_token,
        "name": user.get("name")
    }), 201

@api.route('/api/me', methods=['GET'])
@jwt_required
def get_current_user():
    user = request.user
    return jsonify({
        "user_id": user["_id"],
        "name": user.get("name"),
        "email": user.get("email"),
        "created_at": user.get("created_at")
    }), 200
