from flask import current_app, request, jsonify
import os
import uuid
import datetime
from config import Config
from app import app, storage_service, db
from bson.objectid import ObjectId  

def allowed_file(filename: str) -> bool:
    """Comprueba si la extensión del archivo es permitida."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in Config.ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
def upload_audio():
    """Maneja la subida de un archivo de audio y guarda sus metadatos."""
    # Verificar que el archivo viene en la petición
    if 'file' not in request.files:
        return jsonify({"error": "No se encontró el archivo en la petición"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No se seleccionó ningún archivo"}), 400

    # Validar el tipo de archivo
    if not allowed_file(file.filename):
        return jsonify({"error": "Tipo de archivo no soportado"}), 400

    # Generar un ID único para el archivo
    file_id = str(uuid.uuid4())
    # Conservar la extensión original del archivo
    ext = os.path.splitext(file.filename)[1] 
    object_name = file_id + ext

    # Guardar el archivo en MinIO
    try:
        storage_service.save_file(file, object_name)
    except Exception as e:
        current_app.logger.error(f"Error guardando archivo en MinIO: {e}")
        return jsonify({"error": "Error al guardar el archivo en el almacenamiento"}), 500

    # Preparar metadatos para almacenar en la base de datos
    metadata = {
        "_id": file_id,
        "filename": file.filename,
        "content_type": file.mimetype,
        "bucket": current_app.config["MINIO_BUCKET"],
        "object_name": object_name,
        "size": file.content_length or 0,
        "upload_time": datetime.datetime.utcnow()
    }

    # Guardar metadatos en MongoDB
    try:
        db.save_audio_metadata(metadata)
    except Exception as e:
        # En caso de error al guardar en DB, podría eliminarse el archivo de MinIO (no implementado)
        current_app.logger.error(f"Error guardando metadatos en MongoDB: {e}")
        return jsonify({"error": "Error al guardar metadatos en la base de datos"}), 500

    # Responder con éxito
    return jsonify({"message": "Archivo subido exitosamente", "id": file_id}), 201


@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    """Endpoint para transcribir un audio ya subido usando Whisper."""
    from app import whisper_service  # Importación tardía para evitar import circular
    import tempfile
    import os

    # Obtener ID del audio del formulario o JSON
    audio_id = request.form.get("id") or request.json.get("id")
    if not audio_id:
        return jsonify({"error": "ID de audio no proporcionado"}), 400

    # Buscar en MongoDB
    audio_doc = db.find_audio_by_id(audio_id)
    if not audio_doc:
        return jsonify({"error": "Audio no encontrado"}), 404

    # Descargar el archivo de MinIO a un archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        storage_service.download_file(audio_doc["object_name"], tmp_file.name)

    try:
        # Cargar modelo Whisper si no está cargado
        whisper_service.ensure_model_loaded()

        # Realizar transcripción
        transcription = whisper_service.transcribe_audio(tmp_file.name)

        # Guardar transcripción en MongoDB
        db.update_audio_transcription(audio_id, transcription)

        # Devolver resultado
        return jsonify({
            "message": "Transcripción completada",
            "transcription": transcription
        }), 200
    finally:
        # Borrar el archivo temporal
        os.remove(tmp_file.name)