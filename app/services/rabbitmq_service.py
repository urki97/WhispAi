import pika

rabbit_connection = None
queue_name = 'audios'

def get_rabbit_connection():
    global rabbit_connection
    if rabbit_connection is None or rabbit_connection.is_closed:
        credentials = pika.PlainCredentials("admin", "admin")
        rabbit_connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="localhost", credentials=credentials)
        )
    return rabbit_connection

def publish_message(message):
    if rabbit_connection is None or rabbit_connection.is_closed:
        get_rabbit_connection()

    channel = rabbit_connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # Make message persistent
        )
    )