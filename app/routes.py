import os
import uuid
import datetime
import tempfile
import threading

from flask import current_app, request, jsonify
from pydub.utils import mediainfo

from config import Config
from app import app, storage_service, db, whisper_service
from app.jwt_utils import generate_jwt, jwt_required
from app.llm_utils import generate_summary
from app.whisper_service import transcribe_audio



### UTILIDADES ###

def allowed_file(filename: str) -> bool:
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in Config.ALLOWED_EXTENSIONS

def format_transcription(text: str, output_format: str) -> str:
    if output_format == "text":
        return text.strip()
    elif output_format == "sentences":
        return text.replace('. ', '.\n').strip()
    elif output_format == "summary":
        return "[Resumen no implementado]"
    elif output_format == "actions":
        return "[Acciones no implementadas]"
    else:
        return text.strip()

def map_precision_to_model(precision: str) -> str:
    return {
        "fast": "small",
        "balanced": "medium",
        "accurate": "base"
    }.get(precision, "base")

def select_model_by_duration(duration: float) -> str:
    if duration < 30:
        return "small"
    elif duration < 90:
        return "medium"
    else:
        return "base"

def get_audio_duration(file_path: str) -> float:
    try:
        info = mediainfo(file_path)
        return float(info['duration'])
    except Exception as e:
        current_app.logger.warning(f"No se pudo obtener duración del audio: {e}")
        return 0.0

def background_transcription(audio_id: str, object_name: str, mode: str = "accurate", output_format: str = "text"):
    with app.app_context():
        tmp_file = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                storage_service.download_file(object_name, tmp_file.name)

            duration = get_audio_duration(tmp_file.name)

            def map_precision_to_model(precision: str) -> str:
                return {
                    "fast": "small",
                    "balanced": "medium",
                    "accurate": "base"
                }.get(precision, "base")

            if mode in ["fast", "balanced", "accurate"]:
                model_name = map_precision_to_model(mode)
            else:
                model_name = select_model_by_duration(duration)

            whisper_service.ensure_model_loaded(model_name)

            language = whisper_service.detect_language(tmp_file.name)
            transcription = transcribe_audio(tmp_file.name)
            transcription = format_transcription(transcription, output_format)

            audio_doc = db.find_audio_by_id(audio_id)
            summary = None
            summary_type = audio_doc.get("summary_type", "short")

            if audio_doc.get("generate_summary"):
                summary = generate_summary(transcription, summary_type)

            db.update_audio_transcription(audio_id, transcription, language, summary=summary)
            db.update_audio_metadata(audio_id, {
                "duration": duration,
                "model_used": model_name,
                "summary_type": summary_type
            })
            db.update_audio_status(audio_id, "completed")

            current_app.logger.info(f"Transcripción completada para audio ID {audio_id}")

        except Exception as e:
            error_message = str(e)
            current_app.logger.error(f"Error en transcripción background para {audio_id}: {error_message}")
            db.update_audio_status(audio_id, "failed", error_message)

        finally:
            if tmp_file and os.path.exists(tmp_file.name):
                os.remove(tmp_file.name)



### RUTAS API ###

@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email y contraseña requeridos"}), 400

    user = db.get_user_by_email(data["email"])
    if not user or not db.verify_password(user["password_hash"], data["password"]):
        return jsonify({"error": "Credenciales inválidas"}), 401

    token = generate_jwt(user["_id"], user.get("name"))
    return jsonify({
        "user_id": user["_id"],
        "jwt": token,
        "name": user.get("name")
    }), 200

@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json()
    try:
        user = db.create_user(
            name=data.get("name"),
            email=data.get("email"),
            password=data.get("password")
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    token = generate_jwt(user["_id"], user.get("name"))
    return jsonify({
        "user_id": user["_id"],
        "jwt": token,
        "name": user.get("name")
    }), 201

@app.route('/api/me', methods=['GET'])
@jwt_required
def get_current_user():
    user = request.user 
    return jsonify({
        "user_id": user["_id"],
        "name": user.get("name"),
        "email": user.get("email"),
        "created_at": user.get("created_at")
    }), 200

@app.route('/api/upload', methods=['POST'])
@jwt_required
def upload_audio():
    if 'file' not in request.files:
        return jsonify({"error": "No se encontró el archivo en la petición"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No se seleccionó ningún archivo"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Tipo de archivo no soportado"}), 400

    mode = request.form.get("mode") or "auto"
    output_format = request.form.get("format") or "text"
    generate_summary = request.form.get("generate_summary", "false").lower() == "true"
    summary_type = request.form.get("summary_type", "short")

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
        "owner_id": request.user["_id"],
        "generate_summary": generate_summary,
        "summary_type": summary_type,
    }

    try:
        db.save_audio_metadata(metadata)
    except Exception as e:
        current_app.logger.error(f"Error guardando metadatos en MongoDB: {e}")
        return jsonify({"error": "Error al guardar metadatos en la base de datos"}), 500

    thread = threading.Thread(target=background_transcription, args=(file_id, object_name, mode, output_format))
    thread.start()

    return jsonify({
        "message": "Archivo subido correctamente. Transcripción en proceso...",
        "id": file_id,
        "mode": mode
    }), 202


@app.route('/api/result/<audio_id>', methods=['GET'])
@jwt_required
def get_transcription_result(audio_id):
    audio_doc = db.find_audio_by_id(audio_id)
    if not audio_doc:
        return jsonify({"error": "Audio no encontrado"}), 404

    if audio_doc.get("owner_id") != request.user["_id"]:
        return jsonify({"error": "Acceso no autorizado"}), 403

    response = {
        "id": audio_id,
        "status": audio_doc.get("status", "processing"),
        "format": audio_doc.get("output_format", "text"),
        "transcription": audio_doc.get("transcription"),
        "duration": audio_doc.get("duration"),
        "model_used": audio_doc.get("model_used"),
        "language": audio_doc.get("language", "unknown"),
        "generate_summary": audio_doc.get("generate_summary", False),
        "summary_type": audio_doc.get("summary_type", "short"),
        "summary": audio_doc.get("summary")
}


    if audio_doc.get("error_message"):
        response["error_message"] = audio_doc["error_message"]

    return jsonify(response), 200


@app.route('/api/list', methods=['GET'])
@jwt_required
def list_audios():
    audios = db.list_audios_by_user_id(request.user["_id"])
    result = [{
        "id": a["_id"],
        "filename": a.get("filename"),
        "status": a.get("status"),
        "upload_time": a.get("upload_time"),
        "format": a.get("output_format")
    } for a in audios]
    return jsonify(result), 200

@app.route('/api/audio/<audio_id>', methods=['DELETE'])
@jwt_required
def delete_audio(audio_id):
    audio_doc = db.find_audio_by_id(audio_id)
    if not audio_doc:
        return jsonify({"error": "Audio no encontrado"}), 404

    if audio_doc.get("owner_id") != request.user["_id"]:
        return jsonify({"error": "Acceso no autorizado"}), 403

    try:
        storage_service.delete_file(audio_doc["object_name"])
        db.delete_audio(audio_id)
        current_app.logger.info(f"Audio eliminado: {audio_id}")
        return jsonify({"message": "Audio eliminado correctamente"}), 200
    except Exception as e:
        current_app.logger.error(f"Error al eliminar audio {audio_id}: {e}")
        return jsonify({"error": "No se pudo eliminar el audio"}), 500
