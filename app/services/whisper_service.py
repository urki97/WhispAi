# app/whisper_service.py

try:
    import whisper
except ImportError:
    whisper = None

from flask import current_app
from config import Config

model = None
current_model_name = None

def ensure_model_loaded(model_name: str = None):
    """Carga el modelo Whisper solo si aún no está cargado o si cambia el nombre."""
    global model, current_model_name
    if whisper is None:
        raise ImportError("La biblioteca Whisper no está instalada.")

    # Usa el modelo por defecto si no se especifica
    model_name = model_name or Config.WHISPER_MODEL

    if model is None or model_name != current_model_name:
        model = whisper.load_model(model_name)
        current_model_name = model_name

def transcribe_audio(file_path: str) -> str:
    """Transcribe un archivo de audio usando el modelo cargado."""
    if model is None:
        raise RuntimeError("Modelo Whisper no cargado.")

    result = model.transcribe(file_path)
    return result["text"]

def detect_language(file_path: str) -> str:
    """Detecta el idioma predominante del audio usando Whisper."""
    if model is None:
        raise RuntimeError("Modelo Whisper no cargado.")

    result = model.transcribe(file_path, language=None)
    return result.get("language", "unknown")

def get_model_name() -> str:
    """Devuelve el nombre del modelo cargado actualmente."""
    return current_model_name or "none"

def get_model_device_info() -> str:
    """Devuelve información del dispositivo usado por el modelo."""
    if model is None:
        return "none"
    return f"{model.device} ({model.device_index})"

def get_model_parameters() -> str:
    """Devuelve el número de parámetros del modelo (si es accesible)."""
    try:
        return str(model.num_parameters)
    except AttributeError:
        return "unknown"
