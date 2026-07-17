#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Load .env
set -a; source .env; set +a

DB_NAME="${TRYTON_DB_NAME:-tryton}"
ADMIN_PASS="${TRYTON_ADMIN_PASSWORD:-admin_secret}"

echo "==> Inicializando base de datos Tryton: $DB_NAME"
echo "    (Se pedirá la contraseña de admin si no está en .env)"

docker compose run --rm tryton \
    trytond-admin \
        --config /etc/trytond.conf \
        --database "$DB_NAME" \
        --all \
        --password "$ADMIN_PASS"

echo "==> Base de datos inicializada correctamente."
echo "    Levanta Tryton con: docker compose up -d tryton"
echo "    Accede en:          http://localhost:${TRYTON_PORT:-8000}"
