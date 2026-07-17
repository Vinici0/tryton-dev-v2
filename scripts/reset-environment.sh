#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "ADVERTENCIA: Esto eliminará todos los contenedores, imágenes locales y el volumen de PostgreSQL."
read -r -p "¿Continuar? (escribe 'si' para confirmar): " CONFIRM
if [ "$CONFIRM" != "si" ]; then
    echo "Operación cancelada."
    exit 0
fi

echo "==> Deteniendo y eliminando contenedores..."
docker compose down --volumes --remove-orphans

echo "==> Eliminando imagen local de Tryton..."
IMAGE_NAME="$(docker compose config --format json | python3 -c "import sys,json; cfg=json.load(sys.stdin); print(list(cfg['services'].values())[1].get('image',''))" 2>/dev/null || true)"
if [ -n "$IMAGE_NAME" ]; then
    docker rmi "$IMAGE_NAME" 2>/dev/null || true
else
    # Fallback: remove by label
    docker compose down --rmi local 2>/dev/null || true
fi

echo "==> Entorno eliminado. Ejecuta './scripts/init-environment.sh' para reconstruir."
