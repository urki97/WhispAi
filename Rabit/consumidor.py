import pika
import time

# Configurar credenciales
credentials = pika.PlainCredentials('admin', 'admin')
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost', port=5672, credentials=credentials)
)
channel = connection.channel()

# Asegurarse de que la cola exista
channel.queue_declare(queue='audios', durable=True)

# Prefetch máximo de 4 sin ack
channel.basic_qos(prefetch_count=4)

def callback(ch, method, properties, body):
    mensaje = body.decode()
    print(f"📥 Recibido: {mensaje}")
    
    # Simular procesamiento
    time.sleep(2)

    # Confirmar recepción
    ch.basic_ack(delivery_tag=method.delivery_tag)
    print(f"✅ Procesado: {mensaje}")

# Consumidor con ack manual
channel.basic_consume(queue='audios', on_message_callback=callback)

print("🟢 Esperando mensajes (máximo 4 a la vez)... Ctrl+C para salir.")
try:
    channel.start_consuming()
except KeyboardInterrupt:
    print("\n❌ Interrumpido.")
    channel.stop_consuming()
    connection.close()
