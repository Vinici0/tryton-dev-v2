# Tryton 8.0 — Entorno de Desarrollo Docker

Stack: PostgreSQL 16 + trytond 8.0 + SAO (cliente web).

## Requisitos

- Docker Desktop con Docker Compose V2
- Git

## Levantar el proyecto

### 1. Clonar el repositorio

```bash
git clone https://github.com/Vinici0/tryton-dev-v2.git
cd tryton-dev-v2
```

### 2. Crear el archivo de entorno

```bash
cp .env.example .env
```

Edita `.env` y cambia las contraseñas:

```
POSTGRES_PASSWORD=tu_password
TRYTON_ADMIN_PASSWORD=tu_password_admin
```

### 3. Construir las imágenes

```bash
docker compose build
```

> La primera vez tarda varios minutos porque compila el cliente web SAO desde el código fuente.

### 4. Inicializar la base de datos

```bash
docker compose up -d postgres
docker compose run --rm tryton trytond-admin -d tryton --all
```

Cuando pregunte por la contraseña del admin, ingresa la misma que pusiste en `TRYTON_ADMIN_PASSWORD`.

### 5. Levantar todos los servicios

```bash
docker compose up -d
```

### 6. Abrir el cliente web

Abre el navegador en: **http://localhost:8001**

| Campo    | Valor     |
|----------|-----------|
| Database | `tryton`  |
| Usuario  | `admin`   |
| Password | el valor de `TRYTON_ADMIN_PASSWORD` en tu `.env` |

---

## Cargar datos de prueba

Con los servicios corriendo:

```bash
./scripts/seed.sh
```

Crea: moneda, país, empresa, clientes, proveedores, productos y registros de ejemplo. Es idempotente — se puede correr múltiples veces sin duplicar datos.

---

## Módulos personalizados

Los módulos van en la carpeta `modules/`. Cada módulo se instala automáticamente en modo editable al iniciar el contenedor.

**Agregar un nuevo módulo:**

```bash
# Copiar la estructura de mi_modulo como base
cp -r modules/mi_modulo modules/nuevo_modulo

# Instalar en el contenedor sin reiniciar
./scripts/install-module.sh nuevo_modulo

# Activar en la base de datos
docker compose exec -it tryton trytond-admin -d tryton --all
```

**Actualizar un módulo después de cambios en el código:**

```bash
./scripts/update-module.sh mi_modulo
```

---

## Comandos útiles

| Acción | Comando |
|--------|---------|
| Ver logs en tiempo real | `./scripts/logs.sh` |
| Apagar servicios | `docker compose down` |
| Reiniciar un servicio | `docker compose restart tryton` |
| Acceder al contenedor | `docker compose exec tryton bash` |
| Acceder a la BD | `docker compose exec postgres psql -U tryton` |
| Resetear todo (borra datos) | `./scripts/reset-environment.sh` |

---

## Estructura del proyecto

```
.
├── compose.yml              # Definición de servicios
├── Dockerfile               # Imagen trytond
├── Dockerfile.sao           # Imagen SAO (cliente web)
├── nginx-sao.conf           # Proxy nginx SAO → trytond
├── docker-entrypoint.sh     # Genera trytond.conf e instala módulos
├── requirements.txt         # Dependencias Python
├── .env.example             # Plantilla de variables de entorno
├── modules/
│   └── mi_modulo/           # Módulo de ejemplo
└── scripts/
    ├── seed.sh              # Carga datos de prueba
    ├── install-module.sh    # Instala un módulo nuevo
    ├── update-module.sh     # Actualiza módulo tras cambios
    ├── logs.sh              # Ver logs
    └── reset-environment.sh # Resetear entorno completo
```
