from flask import Blueprint

api = Blueprint("api", __name__)

from app.routes import auth_routes, manage_routes, upload_routes
