

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

def background_transcription(audio_id: str, object_name: str, mode: str = "accurate", output_format: str = "text"):
    """Procesa la transcripción en segundo plano, aplicando el formato deseado."""
    import tempfile
    from app import app

    with app.app_context():
        tmp_file = None
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
            transcription = format_transcription(transcription, output_format)

            db.update_audio_transcription(audio_id, transcription)
            db.update_audio_status(audio_id, "completed")

            current_app.logger.info(f"Transcripción completada para audio ID {audio_id}")

        except Exception as e:
            error_message = str(e)
            current_app.logger.error(f"Error en transcripción background para {audio_id}: {error_message}")
            db.update_audio_status(audio_id, "failed", error_message)

        finally:
            if tmp_file and os.path.exists(tmp_file.name):
                os.remove(tmp_file.name)


def format_transcription(text: str, output_format: str) -> str:
    """Formatea la transcripción según el formato solicitado."""
    if output_format == "text":
        return text.strip()
    elif output_format == "sentences":
        sentences = text.replace('. ', '.\n')
        return sentences.strip()
    elif output_format == "summary":
        return "[Resumen no implementado]"
    elif output_format == "actions":
        return "[Acciones no implementadas]"
    else:
        return text.strip()  


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
    output_format = request.form.get("format") or "text"
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
        "status": "processing",
        "output_format": output_format,
    }

    try:
        db.save_audio_metadata(metadata)
    except Exception as e:
        current_app.logger.error(f"Error guardando metadatos en MongoDB: {e}")
        return jsonify({"error": "Error al guardar metadatos en la base de datos"}), 500

    # Lanzar transcripción en background
    thread = threading.Thread(target=background_transcription, args=(file_id, object_name, mode, output_format))
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
    """Consulta el estado, formato y resultado de una transcripción por ID."""
    audio_doc = db.find_audio_by_id(audio_id)
    if not audio_doc:
        return jsonify({"error": "Audio no encontrado"}), 404

    transcription = audio_doc.get("transcription")
    status = audio_doc.get("status", "processing")
    output_format = audio_doc.get("output_format", "text")
    error_message = audio_doc.get("error_message", None)

    response = {
        "id": audio_id,
        "status": status,
        "format": output_format,
        "transcription": transcription
    }

    if error_message:
        response["error_message"] = error_message

    return jsonify(response), 200

@app.route('/api/list', methods=['GET'])
def list_audios():
    """Devuelve una lista de todos los audios registrados."""
    audios = db.list_all_audios()
    result = []

    for audio in audios:
        result.append({
            "id": audio["_id"],
            "filename": audio.get("filename"),
            "status": audio.get("status", "unknown"),
            "upload_time": audio.get("upload_time"),
            "format": audio.get("output_format", "text")
        })

    return jsonify(result), 200

@app.route('/api/audio/<audio_id>', methods=['DELETE'])
def delete_audio(audio_id):
    """Elimina un audio de MinIO y su entrada en MongoDB."""
    audio_doc = db.find_audio_by_id(audio_id)
    if not audio_doc:
        return jsonify({"error": "Audio no encontrado"}), 404

    try:
        # Eliminar de MinIO
        storage_service.delete_file(audio_doc["object_name"])

        # Eliminar de MongoDB
        db.delete_audio(audio_id)

        current_app.logger.info(f"Audio eliminado: {audio_id}")
        return jsonify({"message": "Audio eliminado correctamente"}), 200

    except Exception as e:
        current_app.logger.error(f"Error al eliminar audio {audio_id}: {e}")
        return jsonify({"error": "No se pudo eliminar el audio"}), 500
