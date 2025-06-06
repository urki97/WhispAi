import os
from dotenv import load_dotenv
from pathlib import Path

# Detectar entorno y cargar variables del archivo correcto
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env.local"

# Si se detecta variable o se fuerza manualmente, usa .env.docker
if os.getenv("USE_DOCKER_ENV", "").lower() == "true":
    ENV_FILE = BASE_DIR / ".env.docker"

# Cargar las variables de entorno desde el archivo adecuado
load_dotenv(dotenv_path=ENV_FILE)

class Config:
    """Configuración centralizada para Flask y servicios externos."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key")
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/whispai")

    # JWT
    JWT_SECRET = os.getenv("JWT_SECRET", "supersecreta")
    JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))
    JWT_REFRESH_DAYS = int(os.getenv("JWT_REFRESH_DAYS", "7"))

    # MinIO
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET = os.getenv("MINIO_BUCKET", "audios")
    MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

    # Archivos
    MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS = {"wav", "mp3", "ogg", "m4a", "mp4", "WMA"}

    # Whisper
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

    # LLM / Open WebUI
    OPEN_WEBUI_HOST = os.getenv("OPEN_WEBUI_HOST", "http://localhost:8080")
    LLM_API_KEY = os.getenv("LLM_API_KEY")
    LLM_DEFAULT_MODEL = os.getenv("LLM_MODEL", "WhispAi Resumen")

    # RabbitMQ
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "192.168.58.103")
    RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
    RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "admin")

    # Formatos de salida LLM permitidos
    ALLOWED_FORMATS = {"text", "summary", "keypoints", "interview", "sentences"}
