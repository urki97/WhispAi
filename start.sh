#!/bin/bash

# Crea la red solo si no existe
if ! docker network ls | grep -q whispai_net; then
  echo "🔧 Creando red Docker 'whispai_net'..."
  docker network create whispai_net
else
  echo "✅ Red 'whispai_net' ya existe."
fi

# Levantar servicios
echo "🚀 Iniciando RabbitMQ..."
cd rabbitmq
docker compose up -d

cd ..
echo "🚀 Iniciando Backend..."
docker compose up -d --build
