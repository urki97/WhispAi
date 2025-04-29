# app/whisper_service.py
try:
    import whisper
except ImportError:
    whisper = None

from flask import current_app

model = None
current_model_name = None

def ensure_model_loaded(model_name: str = "base"):
    """Carga el modelo Whisper solo si aún no está cargado."""
    global model, current_model_name
    if model is None or (model_name and model_name != current_model_name):
        if whisper is None:
            raise ImportError("La biblioteca Whisper no está instalada.")
        if model_name is None:
            model_name = current_app.config.get("WHISPER_MODEL", "base")
        model = whisper.load_model(model_name)
        current_model_name = model_name

def transcribe_audio(file_path: str) -> str:
    """Transcribe un archivo de audio usando Whisper."""
    if model is None:
        raise RuntimeError("Modelo Whisper no cargado.")
    result = model.transcribe(file_path)
    return result["text"]
