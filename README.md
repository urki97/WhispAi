# 📘 Documentación de la API - WhispAi

## 🌐 Base URL



---

## 🔐 Autenticación

### POST `/register`

Crea un nuevo usuario.

**Body (JSON):**
```json
{
  "name": "Juan",
  "email": "juan@example.com",
  "password": "123456"
}
```

**Response:**
```json
{
  "user_id": "<uuid>",
  "jwt": "<token_jwt>",
  "name": "Juan"
}
```

---

### POST `/login`

Inicia sesión con email y contraseña.

**Body (JSON):**
```json
{
  "email": "juan@example.com",
  "password": "123456"
}
```

**Response:**
```json
{
  "user_id": "<uuid>",
  "jwt": "<token_jwt>",
  "name": "Juan"
}
```

---

### GET `/me`

Devuelve los datos del usuario autenticado.

**Headers:**
```
Authorization: Bearer <jwt>
```

**Response:**
```json
{
  "user_id": "<uuid>",
  "name": "Juan",
  "email": "juan@example.com",
  "created_at": "2025-05-05T12:00:00Z"
}
```

---

## 🎙️ Audio y Transcripción

### POST `/upload`

Sube un archivo de audio y lanza la transcripción en background.

**Headers:**
```
Authorization: Bearer <jwt>
```

**Form Data:**
- `file`: archivo `.mp3`, `.wav`, etc.
- `mode`: `"fast"`, `"balanced"`, `"accurate"` (opcional, por defecto usa duración).
- `format`: `"text"`, `"sentences"`, `"summary"` (opcional).

**Response:**
```json
{
  "message": "Archivo subido correctamente. Transcripción en proceso...",
  "id": "<uuid_audio>",
  "mode": "balanced"
}
```

---

### GET `/result/<audio_id>`

Devuelve el resultado de una transcripción.

**Headers:**
```
Authorization: Bearer <jwt>
```

**Response (en procesamiento):**
```json
{
  "id": "<uuid_audio>",
  "status": "processing",
  "format": "text",
  "transcription": null
}
```

**Response (completado):**
```json
{
  "id": "<uuid_audio>",
  "status": "completed",
  "format": "text",
  "transcription": "Texto transcrito aquí..."
}
```

---

### GET `/list`

Devuelve una lista de todos los audios subidos por el usuario.

**Headers:**
```
Authorization: Bearer <jwt>
```

**Response:**
```json
[
  {
    "id": "<uuid_audio>",
    "filename": "audio1.mp3",
    "status": "completed",
    "upload_time": "2025-05-05T12:00:00Z",
    "format": "text"
  },
  ...
]
```

---

### DELETE `/audio/<audio_id>`

Elimina un archivo de audio y sus metadatos.

**Headers:**
```
Authorization: Bearer <jwt>
```

**Response:**
```json
{
  "message": "Audio eliminado correctamente"
}
```

---

## ℹ️ Notas técnicas

- **Duración y modelo:** si no se especifica `mode`, el sistema selecciona el modelo automáticamente según duración del audio:
  - `<30s`: `small`
  - `<90s`: `medium`
  - `>90s`: `base`
- **Formatos de salida soportados:**
  - `"text"`: texto plano (implementado)
  - `"sentences"`: una oración por línea (implementado)
  - `"summary"`, `"actions"`: placeholders para futuras versiones

---
