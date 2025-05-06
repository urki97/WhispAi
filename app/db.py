import datetime
import uuid
from pymongo import MongoClient
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

mongo_client = None
mongo_db = None

def init_db(app):
    """Inicializa la conexión a la base de datos MongoDB."""
    global mongo_client, mongo_db
    uri = app.config["MONGO_URI"]
    mongo_client = MongoClient(uri)
    mongo_db = mongo_client.get_default_database()
    if mongo_db is None:
        mongo_db = mongo_client["whispai"]
    return mongo_db

def require_db():
    if mongo_db is None:
        raise RuntimeError("Base de datos no inicializada")

### Usuarios ###

def create_user(name: str = None, email: str = None, password: str = None) -> dict:
    """Crea un nuevo usuario con email y contraseña (opcional nombre)."""
    require_db()
    if not email or not password:
        raise ValueError("Email y contraseña requeridos")

    if mongo_db["users"].find_one({"email": email}):
        raise ValueError("El email ya está registrado")

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

def get_user_by_id(user_id: str) -> dict | None:
    require_db()
    return mongo_db["users"].find_one({"_id": user_id})

def get_user_by_email(email: str) -> dict | None:
    require_db()
    return mongo_db["users"].find_one({"email": email})

def verify_password(stored_hash: str, password: str) -> bool:
    return check_password_hash(stored_hash, password)

### Audios ###

def save_audio_metadata(metadata: dict):
    require_db()
    result = mongo_db["audios"].insert_one(metadata)
    return result.inserted_id

def update_audio_metadata(audio_id: str, data: dict):
    require_db()
    mongo_db["audios"].update_one({"_id": audio_id}, {"$set": data})

def find_audio_by_id(audio_id: str):
    require_db()
    return mongo_db["audios"].find_one({"_id": audio_id})

def update_audio_transcription(audio_id, transcription_text):
    require_db()
    mongo_db["audios"].update_one(
        {"_id": audio_id},
        {"$set": {"transcription": transcription_text}}
    )

def update_audio_status(audio_id: str, status: str, error_message: str = None):
    require_db()
    update_data = {"status": status}
    if error_message:
        update_data["error_message"] = error_message
    mongo_db["audios"].update_one({"_id": audio_id}, {"$set": update_data})

def list_audios_by_user_id(user_id: str):
    require_db()
    return list(mongo_db["audios"].find({"owner_id": user_id}))

def delete_audio(audio_id: str):
    require_db()
    mongo_db["audios"].delete_one({"_id": audio_id})
