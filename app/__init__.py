import os
import logging
from flask import Flask
from config import Config
from logging.handlers import RotatingFileHandler

def create_app():
    """Crea y configura la instancia de la app Flask."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar servicios
    from app import db
    from app.services import storage_service
    db.init_db(app)
    storage_service.init_storage(app)

    setup_logging(app)

    # Registrar Blueprints
    from app.routes import api
    app.register_blueprint(api)

    return app

def setup_logging(app):
    """Configura logging profesional para WhispAi."""
    if not os.path.exists('logs'):
        os.mkdir('logs')

    info_handler = RotatingFileHandler('logs/whispai_info.log', maxBytes=10 * 1024 * 1024, backupCount=5)
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [%(pathname)s:%(lineno)d]'
    ))

    error_handler = RotatingFileHandler('logs/whispai_error.log', maxBytes=5 * 1024 * 1024, backupCount=3)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [%(pathname)s:%(lineno)d]'
    ))

    app.logger.addHandler(info_handler)
    app.logger.addHandler(error_handler)
    app.logger.setLevel(logging.DEBUG)
    app.logger.info('WhispAi startup')

# Reexportar servicios para uso externo (como consumidor.py)
from app import db as db
from app.services import storage_service as storage_service
from app.services import whisper_service as whisper_service
