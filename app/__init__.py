from flask import Flask
from config import Config

# Crear instancia de Flask
app = Flask(__name__)
app.config.from_object(Config)

# Inicializar conexiones de servicios básicos
from . import db, storage_service
db.init_db(app)
storage_service.init_storage(app)

# Importar rutas
from . import routes
