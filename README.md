README

apuntes por el momento:

Si quieres rápido:

bash
Copiar
Editar
curl -X POST http://localhost:5000/api/transcribe -F "id=<ID>" -F "mode=fast"
Si quieres normal:

bash
Copiar
Editar
curl -X POST http://localhost:5000/api/transcribe -F "id=<ID>"
Si quieres largo:

bash
Copiar
Editar
curl -X POST http://localhost:5000/api/transcribe -F "id=<ID>" -F "mode=longtext"