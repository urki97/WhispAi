import requests
from config import Config

FORMAT_TO_MODEL = {
    "summary": "WhispAi Resumen",
    "keypoints": "WhispAi MindMap",
    "interview": "WhispAi Prueba",
    "text": Config.LLM_DEFAULT_MODEL
}

def generate_llm_output(text: str, output_format: str, language: str = "unknown") -> str:
    if not text:
        return "[Salida no disponible: texto vacío]"

    model_name = FORMAT_TO_MODEL.get(output_format, Config.LLM_DEFAULT_MODEL)

    headers = {
        "Content-Type": "application/json",
        "Authorization": Config.LLM_API_KEY  # ya incluye el "Bearer ..."
    }

    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": text}],
        "stream": False
    }

    try:
        response = requests.post(
            f"{Config.OPEN_WEBUI_HOST}/api/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    except Exception as e:
        return f"[Error LLM: {str(e)}]"
