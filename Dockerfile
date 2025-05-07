# Usa una imagen de Python ligera
FROM python:3.11-slim

# Evita problemas con el input interactivo en contenedores
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establece el directorio de trabajo
WORKDIR /app

# Instala dependencias del sistema necesarias para audio y compilación
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia los archivos de la app
COPY . /app

# Instala las dependencias de Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Expone el puerto de Flask
EXPOSE 5000

# Comando por defecto para lanzar la app
CMD ["flask", "run", "--host=0.0.0.0"]
