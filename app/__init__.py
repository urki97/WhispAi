from flask import Flask
from config import Config
import logging
from logging.handlers import RotatingFileHandler
import os

# Crear instancia de Flask
app = Flask(__name__)
app.config.from_object(Config)

# Inicializar conexiones de servicios básicos
from . import db, storage_service
db.init_db(app)
storage_service.init_storage(app)

# Importar rutas
from . import routes

import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(app):
    """Configura logging profesional para WhispAi."""

    if not os.path.exists('logs'):
        os.mkdir('logs')

    # Log de INFO y DEBUG
    info_handler = RotatingFileHandler('logs/whispai_info.log', maxBytes=10 * 1024 * 1024, backupCount=5)
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [%(pathname)s:%(lineno)d]'
    ))

    # Log solo de errores
    error_handler = RotatingFileHandler('logs/whispai_error.log', maxBytes=5 * 1024 * 1024, backupCount=3)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [%(pathname)s:%(lineno)d]'
    ))

    # Añadir handlers al logger
    app.logger.addHandler(info_handler)
    app.logger.addHandler(error_handler)
    app.logger.setLevel(logging.DEBUG) 

    app.logger.info('WhispAi startup')

# Llamar a setup_logging después de crear la app
setup_logging(app)