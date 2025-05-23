import pika
import json
import os

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "admin")

def send_audio_task(payload: dict):
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
        properties=pika.BasicProperties(delivery_mode=2)  # persistente
    )

    print(f"Mensaje enviado a RabbitMQ: {payload}")
    connection.close()
