from flask import Blueprint

api = Blueprint("api", __name__)

from app.routes import rabbitmq_service, storage_service, whisper_service 
