#!/bin/bash

set -e  # Termina si hay un error

echo "🔻 Deteniendo y eliminando contenedores, redes y volúmenes..."
docker compose down --volumes 
#--remove-orphans

#echo "🧹 Borrando imágenes dangling y contenedores parados..."
#docker system prune -af

echo "🔧 Reconstruyendo e iniciando servicios..."
docker compose up --build
