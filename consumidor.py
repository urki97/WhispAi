import os
import json
import tempfile
from flask import Flask
from dotenv import load_dotenv
from pathlib import Path
from pydub.utils import mediainfo
import pika

# Cargar .env.local para entorno fuera de Docker
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env.local")

from config import Config
from app import db, storage_service, whisper_service
from app.utils.llm_utils import generate_llm_output
from app.services.whisper_service import transcribe_audio

# Inicializar Flask App (necesario para app_context y configuración)
app = Flask(__name__)
app.config.from_object(Config)

def get_audio_duration(file_path: str) -> float:
    try:
        info = mediainfo(file_path)
        return float(info['duration'])
    except Exception as e:
        print(f"No se pudo obtener duración del audio: {e}")
        return 0.0

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

def process_audio_task(data: dict):
    audio_id = data.get("audio_id")
    object_name = data.get("object_name")
    mode = data.get("mode", "accurate")
    output_format = data.get("output_format", "text")

    tmp_file = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            storage_service.download_file(object_name, tmp_file.name)

        duration = get_audio_duration(tmp_file.name)
        model_name = map_precision_to_model(mode) if mode in ["fast", "balanced", "accurate"] else select_model_by_duration(duration)

        whisper_service.ensure_model_loaded(model_name)
        language = whisper_service.detect_language(tmp_file.name)
        transcription = transcribe_audio(tmp_file.name)

        audio_doc = db.find_audio_by_id(audio_id)
        generate_output = audio_doc.get("generate_llm_output", False)

        if generate_output and output_format in Config.ALLOWED_FORMATS:
            formatted_output = generate_llm_output(transcription, output_format, language)
            llm_model_used = output_format
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
        print(f"Transcripción completada para {audio_id}")

    except Exception as e:
        db.update_audio_status(audio_id, "failed", str(e))
        print(f"Error procesando {audio_id}: {e}")

    finally:
        if tmp_file and os.path.exists(tmp_file.name):
            os.remove(tmp_file.name)

def start_consumidor():
    print("🎧 Iniciando consumidor de RabbitMQ...")

    credentials = pika.PlainCredentials(Config.RABBITMQ_USER, Config.RABBITMQ_PASSWORD)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=Config.RABBITMQ_HOST, credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue="audios", durable=True)
    channel.basic_qos(prefetch_count=4)

    def callback(ch, method, properties, body):
        try:
            data = json.loads(body)
            if not isinstance(data, dict):
                raise ValueError("El mensaje recibido no es un diccionario JSON válido.")
            print(f"Mensaje recibido: {data}")
            process_audio_task(data)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"Error procesando mensaje: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag)


    channel.basic_consume(queue="audios", on_message_callback=callback)
    channel.start_consuming()

if __name__ == "__main__":
    with app.app_context():
        db.init_db(app)
        storage_service.init_storage(app)
        start_consumidor()
