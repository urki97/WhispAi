from flask import Blueprint

api = Blueprint("api", __name__)

from app.routes import jwt_utils, llm_utils, jwt_utils
