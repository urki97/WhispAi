import os
import uuid
import datetime

from flask import request, jsonify, current_app
from config import Config
from app.routes import api
from app import db
from app.services import storage_service
from app.utils.jwt_utils import jwt_required
from rabbitmq.emisor import send_audio_task
from app.utils.llm_utils import generate_llm_output 

@api.route('/api/result/<audio_id>', methods=['GET'])
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
        "generate_llm_output": audio_doc.get("generate_llm_output", True),
        "llm_model_used": audio_doc.get("llm_model_used"),
        "output_text": audio_doc.get("output_text")
    }

    if audio_doc.get("error_message"):
        response["error_message"] = audio_doc["error_message"]

    return jsonify(response), 200

@api.route('/api/reinterpret/<audio_id>', methods=['POST'])
@jwt_required
def reinterpret_audio(audio_id):
    data = request.get_json()
    output_format = data.get("format", "text")

    if output_format not in Config.ALLOWED_FORMATS:
        return jsonify({"error": "Formato de salida no válido"}), 400

    audio_doc = db.find_audio_by_id(audio_id)
    if not audio_doc:
        return jsonify({"error": "Audio no encontrado"}), 404

    if audio_doc.get("owner_id") != request.user["_id"]:
        return jsonify({"error": "Acceso no autorizado"}), 403

    transcription = audio_doc.get("transcription")
    if not transcription:
        return jsonify({"error": "No hay transcripción disponible"}), 400

    language = audio_doc.get("language", "unknown")
    new_output = generate_llm_output(transcription, output_format, language)

    llm_model_used = output_format if output_format in Config.ALLOWED_FORMATS else None

    db.update_audio_transcription(audio_id, transcription_text=transcription, language=language, output_text=new_output)
    db.update_audio_metadata(audio_id, {
        "output_format": output_format,
        "llm_model_used": llm_model_used
    })

    return jsonify({
        "message": "Interpretación actualizada correctamente",
        "output_format": output_format,
        "output_text": new_output,
        "llm_model_used": llm_model_used
    }), 200


@api.route('/api/list', methods=['GET'])
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

@api.route('/api/audio/<audio_id>', methods=['DELETE'])
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
        return jsonify({"message": "Audio eliminado correctamente"}), 200
    except Exception as e:
        current_app.logger.error(f"Error al eliminar audio {audio_id}: {e}")
        return jsonify({"error": "No se pudo eliminar el audio"}), 500
