import os
import requests

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = os.getenv("LLM_MODEL", "mistral")

def generate_summary(text: str, summary_type: str = "short") -> str:
    """Genera un resumen usando el modelo LLM vía Ollama."""
    if not text:
        return "[Resumen no disponible: texto vacío]"

    prompt = f"Resume el siguiente texto con un estilo '{summary_type}' de forma clara, estructurada y concisa:\n\n{text}"

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={"model": MODEL_NAME, "prompt": prompt}
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    except Exception as e:
        return f"[Resumen no disponible: {str(e)}]"
