import jwt
import datetime
from functools import wraps
from flask import current_app, request, jsonify, has_request_context
from app import db
from config import Config

def get_config_value(key: str, default=None):
    """Obtiene configuración desde Flask o Config."""
    if has_request_context() and current_app:
        return current_app.config.get(key, default)
    return getattr(Config, key, default)

def generate_jwt(user_id: str, name: str = None) -> str:
    """Genera un token JWT para un usuario."""
    payload = {
        "sub": user_id,
        "name": name,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(
            minutes=get_config_value("JWT_EXPIRATION_MINUTES", 60)
        )
    }
    return jwt.encode(payload, get_config_value("JWT_SECRET"), algorithm="HS256")

def decode_jwt(token: str, refresh=False) -> dict:
    try:
        payload = jwt.decode(token, get_config_value("JWT_SECRET"), algorithms=["HS256"])
        if refresh and payload.get("type") != "refresh":
            raise ValueError("No es un refresh token")
        return payload
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

def generate_refresh_token(user_id: str) -> str:
    """Genera un refresh token JWT de larga duración."""
    payload = {
        "sub": user_id,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(
            days=get_config_value("JWT_REFRESH_DAYS", 30)
        ),
        "type": "refresh"
    }
    return jwt.encode(payload, get_config_value("JWT_SECRET"), algorithm="HS256")
