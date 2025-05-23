import os
from dotenv import load_dotenv

load_dotenv()  # Cargar variables de entorno desde .env

class Config:
    """Configuración de la aplicación Flask y servicios externos."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key")
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/whispai")

    # JWT
    JWT_SECRET = os.getenv("JWT_SECRET", "supersecreta")
    JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

    # MinIO
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET = os.getenv("MINIO_BUCKET", "audios")
    MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

    # Archivos
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS = {"wav", "mp3", "ogg", "m4a"}

    # Whisper
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

    # LLM / Open WebUI
    OPEN_WEBUI_HOST = os.getenv("OPEN_WEBUI_HOST", "http://192.168.1.26:8080")
    LLM_API_KEY = os.getenv("LLM_API_KEY")
    LLM_DEFAULT_MODEL = os.getenv("LLM_MODEL", "WhispAi Resumen")

    # Tipos de formato de salida soportados
    ALLOWED_FORMATS = {"text", "summary", "keypoints", "interview", "sentences"}
