# app/routes.py

from flask import current_app, request, jsonify
import os
import uuid
import datetime
import tempfile
import threading
from config import Config
from app import app, storage_service, db
from app.whisper_service import ensure_model_loaded, transcribe_audio
from bson.objectid import ObjectId

def allowed_file(filename: str) -> bool:
    """Comprueba si la extensión del archivo es permitida."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in Config.ALLOWED_EXTENSIONS

def background_transcription(audio_id: str, object_name: str, mode: str = "accurate"):
    """Procesa la transcripción en segundo plano."""
    import tempfile
    from app import app  # 👈 importar la app

    with app.app_context():  # 👈 Entrar manualmente en contexto Flask
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                storage_service.download_file(object_name, tmp_file.name)

            if mode == "fast":
                ensure_model_loaded("small")
            elif mode == "longtext":
                ensure_model_loaded("medium")
            else:
                ensure_model_loaded("base")

            transcription = transcribe_audio(tmp_file.name)
            db.update_audio_transcription(audio_id, transcription)

            current_app.logger.info(f"Transcripción completada para audio ID {audio_id}")

        except Exception as e:
            current_app.logger.error(f"Error en transcripción background para {audio_id}: {e}")

        finally:
            if os.path.exists(tmp_file.name):
                os.remove(tmp_file.name)


@app.route('/api/upload', methods=['POST'])
def upload_audio():
    """Sube un archivo de audio, guarda metadatos y lanza transcripción en background."""

    if 'file' not in request.files:
        return jsonify({"error": "No se encontró el archivo en la petición"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No se seleccionó ningún archivo"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Tipo de archivo no soportado"}), 400

    mode = request.form.get("mode") or "accurate"

    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    object_name = file_id + ext

    try:
        storage_service.save_file(file, object_name)
    except Exception as e:
        current_app.logger.error(f"Error guardando archivo en MinIO: {e}")
        return jsonify({"error": "Error al guardar el archivo en almacenamiento"}), 500

    metadata = {
        "_id": file_id,
        "filename": file.filename,
        "content_type": file.mimetype,
        "bucket": current_app.config["MINIO_BUCKET"],
        "object_name": object_name,
        "size": file.content_length or 0,
        "upload_time": datetime.datetime.utcnow(),
        "transcription": None,
        "status": "processing"
    }

    try:
        db.save_audio_metadata(metadata)
    except Exception as e:
        current_app.logger.error(f"Error guardando metadatos en MongoDB: {e}")
        return jsonify({"error": "Error al guardar metadatos en la base de datos"}), 500

    # Lanzar transcripción en background
    thread = threading.Thread(target=background_transcription, args=(file_id, object_name, mode))
    thread.start()

    return jsonify({
        "message": "Archivo subido correctamente. Transcripción en proceso...",
        "id": file_id,
        "mode": mode
    }), 202

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio_route():
    """Transcribe un audio ya subido usando Whisper, eligiendo modo."""

    audio_id = request.form.get("id") or (request.json and request.json.get("id"))
    mode = request.form.get("mode") or (request.json and request.json.get("mode")) or "accurate"

    if not audio_id:
        return jsonify({"error": "ID de audio no proporcionado"}), 400

    audio_doc = db.find_audio_by_id(audio_id)
    if not audio_doc:
        return jsonify({"error": "Audio no encontrado"}), 404

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        storage_service.download_file(audio_doc["object_name"], tmp_file.name)

    try:
        if mode == "fast":
            ensure_model_loaded("small")
        elif mode == "longtext":
            ensure_model_loaded("medium")
        else:
            ensure_model_loaded("base")

        transcription = transcribe_audio(tmp_file.name)
        db.update_audio_transcription(audio_id, transcription)

        return jsonify({
            "message": "Transcripción completada",
            "mode": mode,
            "transcription": transcription
        }), 200
    finally:
        os.remove(tmp_file.name)

@app.route('/api/result/<audio_id>', methods=['GET'])
def get_transcription_result(audio_id):
    """Consulta el estado y resultado de una transcripción por ID."""
    audio_doc = db.find_audio_by_id(audio_id)
    if not audio_doc:
        return jsonify({"error": "Audio no encontrado"}), 404

    transcription = audio_doc.get("transcription")
    if transcription:
        status = "completed"
    else:
        status = "processing"

    return jsonify({
        "id": audio_id,
        "status": status,
        "transcription": transcription  # será None si aún no terminó
    }), 200
