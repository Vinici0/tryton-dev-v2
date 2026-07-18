# Tryton 8.0 — Docker Dev

PostgreSQL 16 + trytond 8.0.7 + SAO (cliente web).

## Setup

```bash
cp .env.example .env
docker compose build
docker compose up -d postgres
docker compose run --rm tryton trytond-admin -c /etc/trytond.conf -d tryton --all
docker compose up -d
```

UI → **http://localhost:8001** | DB: `tryton` | User: `admin`

```bash
./scripts/seed.sh   # carga datos de prueba (opcional)
```

## Módulo: `purchase_request`

Solicitudes de compra con flujo de aprobación: **Borrador → Enviada → Aprobada → Atendida**

```bash
./scripts/install-module.sh purchase_request
./scripts/update-module.sh purchase_request
```

## Tests

```bash
docker compose exec tryton python3 -m unittest purchase_request.tests.SubtotalTestCase -v
```

## Comandos

| | |
|---|---|
| Logs | `docker compose logs -f tryton` |
| Reiniciar | `docker compose restart tryton` |
| BD | `docker compose exec postgres psql -U tryton -d tryton` |
| Reset | `./scripts/reset-environment.sh` |

<img width="1700" height="309" alt="image" src="https://github.com/user-attachments/assets/359dfe0c-990d-410e-8173-f3177fac517a" />
<img width="1701" height="552" alt="image" src="https://github.com/user-attachments/assets/00f43431-8ab5-49cb-8ea1-3d5283742f83" />

