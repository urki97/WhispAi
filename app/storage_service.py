import io
from flask import current_app
from minio import Minio
from minio.error import S3Error
from werkzeug.utils import secure_filename

minio_client = None
bucket_name = None

def init_storage(app):
    """Inicializa el cliente de MinIO y asegura que el bucket exista."""
    global minio_client, bucket_name

    minio_client = Minio(
        app.config["MINIO_ENDPOINT"],
        access_key=app.config["MINIO_ACCESS_KEY"],
        secret_key=app.config["MINIO_SECRET_KEY"],
        secure=app.config["MINIO_SECURE"]
    )

    bucket_name = app.config.get("MINIO_BUCKET", "audios")

    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)
        app.logger.info(f"Bucket creado: {bucket_name}")
    else:
        app.logger.debug(f"Bucket ya existente: {bucket_name}")

def save_file(file, object_name=None):
    """Guarda un archivo de audio en MinIO."""
    if minio_client is None:
        raise RuntimeError("Cliente de MinIO no inicializado")

    object_name = object_name or secure_filename(file.filename)
    data = file.read()
    file_size = len(data)

    minio_client.put_object(
        bucket_name,
        object_name,
        io.BytesIO(data),
        file_size,
        content_type=file.mimetype
    )

    return object_name

def download_file(object_name: str, download_path: str):
    """Descarga un objeto de MinIO a una ruta local."""
    if minio_client is None:
        raise RuntimeError("Cliente de MinIO no inicializado")
    minio_client.fget_object(bucket_name, object_name, download_path)

def delete_file(object_name: str):
    """Elimina un objeto del bucket de MinIO."""
    if minio_client is None:
        raise RuntimeError("Cliente de MinIO no inicializado")
    minio_client.remove_object(bucket_name, object_name)
