#!/usr/bin/env bash
# Carga datos de prueba en la base de datos Tryton via Proteus.
# Uso: ./scripts/seed.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "==> Copiando seed.py al contenedor..."
docker compose -f "$PROJECT_DIR/compose.yml" cp \
    "$SCRIPT_DIR/seed.py" tryton:/app/scripts/seed.py

echo "==> Ejecutando seed..."
docker compose -f "$PROJECT_DIR/compose.yml" exec tryton \
    python /app/scripts/seed.py
