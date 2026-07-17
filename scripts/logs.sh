#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

SERVICE="${1:-tryton}"
echo "==> Logs de '$SERVICE' (Ctrl+C para salir)..."
docker compose logs -f "$SERVICE"
