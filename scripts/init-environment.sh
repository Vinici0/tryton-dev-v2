#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "==> Validando arquitectura..."
ARCH="$(uname -m)"
if [ "$ARCH" != "arm64" ]; then
    echo "ADVERTENCIA: arquitectura detectada es '$ARCH', se esperaba arm64."
fi
echo "    Arquitectura: $ARCH"

echo "==> Validando Docker..."
if ! command -v docker &>/dev/null; then
    echo "ERROR: Docker no está instalado o no está en el PATH."
    exit 1
fi
docker version --format 'Docker Engine: {{.Server.Version}}' 2>/dev/null || docker version
docker compose version

echo "==> Construyendo imagen Tryton..."
cd "$PROJECT_DIR"
docker compose build --no-cache

echo "==> Levantando PostgreSQL..."
docker compose up -d postgres

echo "==> Esperando healthcheck de PostgreSQL..."
until docker compose ps postgres | grep -q "healthy"; do
    printf "."
    sleep 2
done
echo ""
echo "    PostgreSQL listo."

echo "==> Entorno inicializado. Ejecuta './scripts/init-db.sh' para crear la base de datos."
