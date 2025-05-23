import os
import requests

OPEN_WEBUI_HOST = os.getenv("OPEN_WEBUI_HOST", "http://host.docker.internal:8080")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "WhispAi Resumen")
API_KEY = os.getenv("LLM_API_KEY")

FORMAT_TO_MODEL = {
    "summary": "WhispAi Resumen",
    "keypoints": "WhispAi MindMap",
    "interview": "WhispAi Prueba",
    "text": DEFAULT_MODEL
}

def generate_llm_output(text: str, output_format: str, language: str = "unknown") -> str:
    if not text:
        return "[Salida no disponible: texto vacío]"

    model_name = FORMAT_TO_MODEL.get(output_format, DEFAULT_MODEL)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": text}],
        "stream": False
    }

    try:
        response = requests.post(f"{OPEN_WEBUI_HOST}/api/chat/completions", json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    except Exception as e:
        return f"[Error LLM: {str(e)}]"
