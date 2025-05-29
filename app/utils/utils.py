import os
import uuid
import datetime
import tempfile
import threading

from flask import current_app, request, jsonify
from pydub.utils import mediainfo

from config import Config
from app import app, storage_service, db, whisper_service
from utils.jwt_utils import generate_jwt, jwt_required
from utils.llm_utils import generate_llm_output
from app.services.whisper_service import transcribe_audio
from app.services.rabbitmq_service import publish_message

def allowed_file(filename: str) -> bool:
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in Config.ALLOWED_EXTENSIONS

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

            if mode in ["fast", "balanced", "accurate"]:
                model_name = map_precision_to_model(mode)
            else:
                model_name = select_model_by_duration(duration)

            whisper_service.ensure_model_loaded(model_name)

            language = whisper_service.detect_language(tmp_file.name)
            transcription = transcribe_audio(tmp_file.name)

            audio_doc = db.find_audio_by_id(audio_id)
            generate_output = audio_doc.get("generate_llm_output", False)

            if generate_output and output_format in ["summary", "keypoints", "interview", "text"]:
                formatted_output = generate_llm_output(transcription, output_format, language)
                llm_model_used = output_format
                current_app.logger.info(f"Salida LLM generada con modelo: {llm_model_used}")
            else:
                formatted_output = transcription.strip()
                llm_model_used = None

            db.update_audio_transcription(
                audio_id,
                transcription_text=transcription,
                language=language,
                output_text=formatted_output
            )

            db.update_audio_metadata(audio_id, {
                "duration": duration,
                "model_used": model_name,
                "language": language,
                "llm_model_used": llm_model_used
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
