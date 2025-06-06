import os
import io
import uuid
import datetime
from flask import request, jsonify, current_app
from config import Config
from app.routes import api
from app import db
from app.services import storage_service
from app.utils.jwt_utils import jwt_required
from rabbitmq.emisor import send_audio_task

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@api.route('/api/upload', methods=['POST'])
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
    generate_llm_output_flag = request.form.get("generate_llm_output", "false").lower() == "true"

    if output_format not in Config.ALLOWED_FORMATS:
        return jsonify({"error": "Formato de salida no válido"}), 400

    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    object_name = f"{file_id}{ext}"

    try:
        data = file.read()
        file.seek(0)
        storage_service.save_file(io.BytesIO(data), object_name)
    except Exception as e:
        current_app.logger.error(f"Error guardando archivo en MinIO: {e}")
        return jsonify({"error": "Error al guardar el archivo en almacenamiento"}), 500

    metadata = {
        "_id": file_id,
        "filename": file.filename,
        "content_type": file.mimetype,
        "bucket": Config.MINIO_BUCKET,
        "object_name": object_name,
        "size": len(data),
        "upload_time": datetime.datetime.utcnow(),
        "transcription": None,
        "status": "processing",
        "output_format": output_format,
        "owner_id": request.user["_id"],
        "generate_llm_output": generate_llm_output_flag,
        "output_text": None,
        "language": "unknown",
        "model_used": None,
        "duration": None
    }

    try:
        db.save_audio_metadata(metadata)
    except Exception as e:
        current_app.logger.error(f"Error guardando metadatos en MongoDB: {e}")
        return jsonify({"error": "Error al guardar metadatos en la base de datos"}), 500

    try:
        send_audio_task({
            "audio_id": file_id,
            "object_name": object_name,
            "output_format": output_format,
            "mode": mode
        })
    except Exception as e:
        current_app.logger.error(f"Error al enviar mensaje a RabbitMQ: {e}")
        return jsonify({"error": "No se pudo enviar la tarea de transcripción"}), 500

    return jsonify({
        "message": "Audio recibido. Procesamiento encolado.",
        "id": file_id,
        "status": "processing"
    }), 202

@api.route('/api/prueba', methods=['POST'])
def prueba_rabbit():
    if 'file' not in request.files:
        return jsonify({"error": "No se encontró el archivo en la petición"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No se seleccionó ningún archivo"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Tipo de archivo no soportado"}), 400

    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    object_name = f"{file_id}{ext}"

    try:
        data = file.read()
        file.seek(0)
        storage_service.save_file(io.BytesIO(data), object_name)

    except Exception as e:
        current_app.logger.error(f"Error guardando archivo en MinIO: {e}")
        return jsonify({"error": "Error al guardar el archivo en almacenamiento"}), 500

    send_audio_task({
        "audio_id": file_id,
        "object_name": object_name,
        "output_format": "text",
        "mode": "auto"
    })

    return jsonify({
        "message": "Archivo subido correctamente y mensaje enviado a RabbitMQ",
        "id": file_id,
        "object_name": object_name
    }), 202
