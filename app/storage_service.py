import io
from minio import Minio
from minio.error import S3Error
from werkzeug.utils import secure_filename

minio_client = None
bucket_name = None

def init_storage(app):
    """Inicializa el cliente de MinIO y asegura que el bucket exista."""
    global minio_client, bucket_name
    # Crear cliente MinIO con los datos de configuración del entorno
    minio_client = Minio(
        app.config["MINIO_ENDPOINT"],
        access_key=app.config["MINIO_ACCESS_KEY"],
        secret_key=app.config["MINIO_SECRET_KEY"],
        secure=app.config["MINIO_SECURE"]
    )
    bucket_name = app.config.get("MINIO_BUCKET", "audios")
    # Crear el bucket en MinIO si no existe
    found = minio_client.bucket_exists(bucket_name)
    if not found:
        minio_client.make_bucket(bucket_name)

def save_file(file, object_name=None):
    """Guarda un archivo de audio en el almacenamiento MinIO."""
    if minio_client is None:
        raise RuntimeError("Cliente de MinIO no inicializado")
    # Determinar un nombre de objeto seguro para almacenar
    if object_name is None:
        object_name = secure_filename(file.filename)
    # Leer datos del archivo en memoria (nota: optimizar con streaming si el archivo es muy grande)
    data = file.read()
    file_size = len(data)
    # Subir el archivo al bucket de MinIO (lanza S3Error si hay errores)
    minio_client.put_object(
        bucket_name,
        object_name,
        io.BytesIO(data),
        file_size,
        content_type=file.mimetype
    )
    return object_name

def download_file(object_name, download_path):
    """Descarga un objeto de MinIO a un archivo local."""
    if minio_client is None:
        raise RuntimeError("Cliente de MinIO no inicializado")
    minio_client.fget_object(bucket_name, object_name, download_path)
