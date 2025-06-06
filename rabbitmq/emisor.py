import os
import sys
import json
import pika

# Asegura que config.py se pueda importar aunque estés en rabbitmq/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import Config

# Configuración desde variables de entorno o config centralizada
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", Config.RABBITMQ_HOST)
RABBITMQ_USER = os.getenv("RABBITMQ_USER", Config.RABBITMQ_USER)
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", Config.RABBITMQ_PASSWORD)

def send_audio_task(payload: dict):
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
        )
        channel = connection.channel()
        channel.queue_declare(queue="audios", durable=True)

        channel.basic_publish(
            exchange='',
            routing_key='audios',
            body=json.dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2)
        )

        print(f"✅ Mensaje enviado a RabbitMQ: {payload}")
        connection.close()
    except Exception as e:
        print(f"❌ Error al enviar a RabbitMQ: {e}")
        raise


# Solo para pruebas rápidas:
if __name__ == "__main__":
    # Cambia estos valores por un audio real ya subido a MinIO y MongoDB
    send_audio_task({
        "object_name": "archivo.wav",
        "mode": "balanced",
        "output_format": "summary"
    })
