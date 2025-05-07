import os
import openai

# Intenta obtener la clave de API desde las variables de entorno
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

def generate_summary(text: str, summary_type: str = "short") -> str:
    """Genera un resumen usando un LLM. Usa el tipo deseado (short, detailed, etc)."""
    if not OPENAI_API_KEY:
        return "[Resumen desactivado: no se ha configurado OPENAI_API_KEY]"

    prompt = f"Resume el siguiente texto en un estilo '{summary_type}' de forma clara y concisa:\n\n{text}"
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[Resumen no disponible: {str(e)}]"

