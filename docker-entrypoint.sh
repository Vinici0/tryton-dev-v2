#!/usr/bin/env bash
set -euo pipefail

# Generate trytond.conf from environment variables
cat > /etc/trytond.conf <<EOF
[database]
uri = postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

[web]
listen = 0.0.0.0:${TRYTON_PORT:-8000}
cors = ${TRYTON_CORS_ORIGIN:-http://localhost:8001}

[session]
timeout = 43200
EOF

# Install editable modules found in /app/modules
for module_dir in /app/modules/*/; do
    if [ -f "${module_dir}pyproject.toml" ] || [ -f "${module_dir}setup.py" ]; then
        echo "[entrypoint] Installing editable: ${module_dir}"
        pip install --no-cache-dir -q -e "${module_dir}"
    fi
done

exec "$@"
