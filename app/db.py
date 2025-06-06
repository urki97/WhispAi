import datetime
import uuid
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

mongo_client = None
mongo_db = None

def init_db(app=None):
    """Inicializa la conexión a la base de datos MongoDB."""
    global mongo_client, mongo_db

    if app:
        uri = app.config["MONGO_URI"]
        db_name = app.config.get("MONGO_DB", "whispai")
    else:
        uri = Config.MONGO_URI
        db_name = "whispai"

    mongo_client = MongoClient(uri)
    mongo_db = mongo_client[db_name]

    # Crear índice único en 'email' para evitar duplicados
    mongo_db["users"].create_index("email", unique=True)

    return mongo_db


def require_db():
    """Lanza error si la base de datos aún no ha sido inicializada."""
    if mongo_db is None:
        raise RuntimeError("Base de datos no inicializada")

# === Usuarios ===

def create_user(name: str = None, email: str = None, password: str = None) -> dict:
    """Crea un nuevo usuario con email y contraseña (opcional nombre)."""
    require_db()

    if not email or not password:
        raise ValueError("Email y contraseña requeridos")

    try:
        user_id = str(uuid.uuid4())
        user_doc = {
            "_id": user_id,
            "name": name,
            "email": email,
            "password_hash": generate_password_hash(password),
            "created_at": datetime.datetime.utcnow()
        }
        mongo_db["users"].insert_one(user_doc)
        return user_doc
    except DuplicateKeyError:
        raise ValueError("El email ya está registrado")

def get_user_by_id(user_id: str) -> dict | None:
    require_db()
    return mongo_db["users"].find_one({"_id": user_id})

def get_user_by_email(email: str) -> dict | None:
    require_db()
    return mongo_db["users"].find_one({"email": email})

def verify_password(stored_hash: str, password: str) -> bool:
    """Verifica una contraseña contra su hash almacenado."""
    return check_password_hash(stored_hash, password)

# === Audios ===

def save_audio_metadata(metadata: dict) -> str:
    """Guarda los metadatos de un nuevo audio."""
    require_db()
    result = mongo_db["audios"].insert_one(metadata)
    return result.inserted_id

def update_audio_metadata(audio_id: str, data: dict):
    """Actualiza campos generales de un documento de audio."""
    require_db()
    mongo_db["audios"].update_one({"_id": audio_id}, {"$set": data})

def find_audio_by_id(audio_id: str) -> dict | None:
    """Recupera un documento de audio por su ID."""
    require_db()
    return mongo_db["audios"].find_one({"_id": audio_id})

def update_audio_transcription(audio_id, transcription_text, language="unknown", output_text=None):
    require_db()
    update_fields = {
        "transcription": transcription_text,
        "language": language
    }
    if output_text:
        update_fields["output_text"] = output_text
    mongo_db["audios"].update_one(
        {"_id": audio_id},
        {"$set": update_fields}
    )

def update_audio_status(audio_id: str, status: str, error_message: str = None):
    """Actualiza el estado del procesamiento de un audio."""
    require_db()
    update_data = {"status": status}
    if error_message:
        update_data["error_message"] = error_message
    mongo_db["audios"].update_one({"_id": audio_id}, {"$set": update_data})

def list_audios_by_user_id(user_id: str) -> list[dict]:
    """Devuelve todos los audios pertenecientes a un usuario."""
    require_db()
    return list(mongo_db["audios"].find({"owner_id": user_id}))

def delete_audio(audio_id: str):
    """Elimina un audio por ID."""
    require_db()
    mongo_db["audios"].delete_one({"_id": audio_id})
