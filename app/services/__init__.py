from flask import Blueprint

api = Blueprint("api", __name__)

from app.services import rabbitmq_service, storage_service, whisper_service 
