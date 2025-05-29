#!/bin/bash

echo "🛑 Deteniendo servicios del backend..."
docker compose down

echo "🛑 Deteniendo RabbitMQ..."
cd rabbitmq
docker compose down
cd ..

echo "✅ Todos los servicios han sido detenidos correctamente."
