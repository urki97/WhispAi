import jwt
import datetime
from flask import current_app, request, jsonify
from functools import wraps
from app import db

def generate_jwt(user_id: str, name: str = None) -> str:
    """Genera un token JWT para un usuario."""
    payload = {
        "sub": user_id,
        "name": name,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(
            minutes=current_app.config["JWT_EXPIRATION_MINUTES"]
        )
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")

def decode_jwt(token: str) -> dict:
    """Decodifica un JWT y devuelve el payload si es válido."""
    try:
        return jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expirado")
    except jwt.InvalidTokenError:
        raise ValueError("Token inválido")

def jwt_required(f):
    """Decorator para proteger rutas con JWT."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token JWT no proporcionado"}), 401

        token = auth_header.split(" ")[1]

        try:
            payload = decode_jwt(token)
        except ValueError as e:
            return jsonify({"error": str(e)}), 401

        user = db.get_user_by_id(payload["sub"])
        if not user:
            return jsonify({"error": "Usuario no válido"}), 403

        request.user = user
        return f(*args, **kwargs)

    return decorated
