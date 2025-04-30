from pymongo import MongoClient

mongo_client = None
mongo_db = None

def init_db(app):
    """Inicializa la conexión a la base de datos MongoDB."""
    global mongo_client, mongo_db
    uri = app.config["MONGO_URI"]
    # Conectar al servidor de MongoDB
    mongo_client = MongoClient(uri)
    # Seleccionar base de datos (si la URI contiene el nombre, lo usará; de lo contrario, usar 'whispai')
    mongo_db = mongo_client.get_default_database()
    if mongo_db is None:
        mongo_db = mongo_client["whispai"]
    return mongo_db

def save_audio_metadata(metadata: dict):
    """Guarda un documento de metadatos de audio en la colección de MongoDB."""
    if mongo_db is None:
        raise RuntimeError("Base de datos no inicializada")
    # Insertar el documento en la colección "audios"
    result = mongo_db["audios"].insert_one(metadata)
    return result.inserted_id

def find_audio_by_id(audio_id):
    """Busca un audio en MongoDB por su _id."""
    if mongo_db is None:
        raise RuntimeError("Base de datos no inicializada")
    return mongo_db["audios"].find_one({"_id": audio_id})

def update_audio_transcription(audio_id, transcription_text):
    """Actualiza un audio en MongoDB agregando la transcripción."""
    if mongo_db is None:
        raise RuntimeError("Base de datos no inicializada")
    mongo_db["audios"].update_one(
        {"_id": audio_id},
        {"$set": {"transcription": transcription_text}}
    )

def update_audio_status(audio_id: str, status: str, error_message: str = None):
    """Actualiza el estado de un audio en MongoDB."""
    update_data = {"status": status}
    if error_message:
        update_data["error_message"] = error_message
    collection.update_one({"_id": audio_id}, {"$set": update_data})
