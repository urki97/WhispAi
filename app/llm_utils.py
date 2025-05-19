import os
import requests

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "mistral")

# Mapea los formatos de salida a modelos personalizados de Ollama
FORMAT_TO_MODEL = {
    "summary": "summary",
    "keypoints": "keypoints",
    "interview": "interview",
    "text": DEFAULT_MODEL        
}

def generate_llm_output(text: str, output_format: str, language: str = "unknown") -> str:
    """Genera una salida personalizada usando LLM según el formato deseado."""

    if not text:
        return "[Salida no disponible: texto vacío]"

    # Prompt base por tipo
    prompts = {
        "summary": f"Resume el siguiente texto de forma clara y concisa:\n\n{text}",
        "keypoints": f"Extrae los puntos clave del siguiente texto:\n\n{text}",
        "interview": f"Reorganiza el texto como una entrevista con preguntas y respuestas:\n\n{text}",
        "sentences": f"Divide el texto en frases separadas por líneas:\n\n{text}",
        "text": text.strip()
    }

    prompt = prompts.get(output_format)
    if not prompt:
        return f"[Formato no soportado: {output_format}]"

    model_name = FORMAT_TO_MODEL.get(output_format, DEFAULT_MODEL)

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={"model": model_name, "prompt": prompt, "stream": False}
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        return f"[Salida no disponible: {str(e)}]"
