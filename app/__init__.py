from flask import Flask
from config import Config
import os
import logging
from logging.handlers import RotatingFileHandler
from . import db, storage_service

# Crear instancia de Flask
app = Flask(__name__)
app.config.from_object(Config)

# Inicializar servicios
db.init_db(app)
storage_service.init_storage(app)

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

# Configurar logs
setup_logging(app)

# ✅ Importar rutas al final para evitar import circular
from . import routes
