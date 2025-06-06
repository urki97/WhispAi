import io
from flask import current_app
from minio import Minio
from minio.error import S3Error
from werkzeug.utils import secure_filename
from config import Config

minio_client = None
bucket_name = None

def init_storage(app=None):
    """Inicializa el cliente de MinIO y asegura que el bucket exista."""
    global minio_client, bucket_name

    if app:
        endpoint = app.config["MINIO_ENDPOINT"]
        access_key = app.config["MINIO_ACCESS_KEY"]
        secret_key = app.config["MINIO_SECRET_KEY"]
        secure = app.config["MINIO_SECURE"]
        bucket_name = app.config.get("MINIO_BUCKET", "audios")
    else:
        endpoint = Config.MINIO_ENDPOINT
        access_key = Config.MINIO_ACCESS_KEY
        secret_key = Config.MINIO_SECRET_KEY
        secure = Config.MINIO_SECURE
        bucket_name = Config.MINIO_BUCKET

    minio_client = Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure
    )

    # Crea el bucket si no existe
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)
        if app:
            app.logger.info(f"Bucket creado: {bucket_name}")
    else:
        if app:
            app.logger.debug(f"Bucket ya existente: {bucket_name}")

def save_file(file, object_name=None):
    if minio_client is None:
        raise RuntimeError("Cliente de MinIO no inicializado")

    try:
        if hasattr(file, "filename"):  # FileStorage
            object_name = object_name or secure_filename(file.filename)
            content_type = file.mimetype
            data = file.read()
        else:  # BytesIO u otro objeto similar
            object_name = object_name or "audio.wav"
            content_type = "application/octet-stream"
            data = file.read()

        file_size = len(data)
        current_app.logger.info(f"📤 Subiendo {object_name} ({file_size} bytes) a MinIO...")

        minio_client.put_object(
            bucket_name,
            object_name,
            io.BytesIO(data),
            file_size,
            content_type=content_type
        )

        return object_name

    except S3Error as e:
        current_app.logger.error(f"❌ Error al subir archivo a MinIO: {e}")
        raise

def download_file(object_name: str, download_path: str):
    if minio_client is None:
        raise RuntimeError("Cliente de MinIO no inicializado")
    minio_client.fget_object(bucket_name, object_name, download_path)

def delete_file(object_name: str):
    if minio_client is None:
        raise RuntimeError("Cliente de MinIO no inicializado")
    minio_client.remove_object(bucket_name, object_name)
