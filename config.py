from dotenv import load_dotenv
load_dotenv()  # Cargar variables de entorno desde .env

import os

class Config:
    """Configuración de la aplicación Flask y servicios externos."""
    # Configuraciones de Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key")
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    # Configuración de MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/whispai")

    # Configuración de MinIO (almacenamiento de archivos)
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET = os.getenv("MINIO_BUCKET", "audios")
    # Interpretar variable de entorno booleana para conexión segura (HTTPS) a MinIO
    MINIO_SECURE = os.getenv("MINIO_SECURE", "False").lower() == "true"

    # Otras configuraciones
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # Tamaño máximo de archivo (50 MB)
    ALLOWED_EXTENSIONS = {"wav", "mp3", "ogg", "m4a"}  # Extensiones permitidas para archivos de audio

    # Parámetro de modelo Whisper (para futura carga de modelos)
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
