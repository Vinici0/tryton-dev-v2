#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

MODULE="${1:-}"
if [ -z "$MODULE" ]; then
    echo "Uso: $0 <nombre_modulo>"
    echo "Ejemplo: $0 mi_modulo"
    exit 1
fi

MODULE_PATH="./modules/$MODULE"
if [ ! -d "$MODULE_PATH" ]; then
    echo "ERROR: No se encontró el directorio '$MODULE_PATH'."
    exit 1
fi

set -a; source .env; set +a
DB_NAME="${TRYTON_DB_NAME:-tryton}"

echo "==> Instalando módulo '$MODULE' en modo editable..."
docker compose run --rm tryton \
    pip install -e "/app/modules/$MODULE"

echo "==> Actualizando lista de módulos en la base de datos '$DB_NAME'..."
docker compose run --rm tryton \
    trytond-admin \
        --config /etc/trytond.conf \
        --database "$DB_NAME" \
        --update "$MODULE"

echo "==> Módulo '$MODULE' instalado. Reinicia Tryton para aplicar cambios:"
echo "    docker compose restart tryton"
