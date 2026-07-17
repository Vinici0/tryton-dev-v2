# Incidencias resueltas — Tryton 8.0 + Docker Compose + Apple Silicon

Registro de todos los errores encontrados al levantar el entorno por primera vez.
Ordenados por aparición.

---

## 0. Aclaración: `localhost:8000` muestra "Method Not Allowed" en el navegador

**No es un error.** `trytond` es un servidor JSON-RPC puro, no sirve HTML. El navegador hace `GET /` y recibe `405` porque el servidor solo acepta `POST` con payload JSON.

El endpoint real de JSON-RPC es `/rpc/` (no `/`). Para usar la interfaz web se necesita el cliente SAO servido por separado.

**Arquitectura correcta:**
```
Navegador → SAO en nginx :8001 → (proxy interno) → trytond :8000 → PostgreSQL
```

---

## 1. Puerto 5432 ocupado en el host

**Error**
```
Bind for 0.0.0.0:5432 failed: port is already allocated
```

**Causa**
PostgreSQL instalado nativamente en macOS (via Homebrew u otro) ocupa el puerto 5432 del host antes de que Docker intente mapearlo.

**Fix**
Eliminar el mapeo de puerto al host en `compose.yml`. Tryton se conecta a PostgreSQL por la red interna de Docker usando el nombre de servicio `postgres:5432`, por lo que el puerto expuesto al host no es necesario para que el entorno funcione.

```yaml
# ANTES (problemático)
ports:
  - "5432:5432"

# DESPUÉS (correcto)
# sin sección ports en el servicio postgres
```

Si se necesita acceso externo (TablePlus, psql desde el Mac), usar un puerto alto que no esté en uso:
```yaml
ports:
  - "15432:5432"
```

---

## 2. `setuptools.backends.legacy` no disponible

**Error**
```
pip._vendor.pyproject_hooks._impl.BackendUnavailable: Cannot import 'setuptools.backends.legacy'
```

**Causa**
`setuptools.backends.legacy` fue introducido en setuptools ≥69.3. La imagen `python:3.12-slim-bookworm` instala una versión anterior de setuptools que no lo incluye.

**Fix**
Usar el backend estándar compatible con todas las versiones de setuptools ≥40:

```toml
# ANTES (problemático)
build-backend = "setuptools.backends.legacy:build"

# DESPUÉS (correcto)
build-backend = "setuptools.build_meta"
```

---

## 3. `No module named 'psycopg_pool'`

**Error**
```
ModuleNotFoundError: No module named 'psycopg_pool'
```

**Causa**
`trytond` 8.0 importa `psycopg_pool` para gestionar el pool de conexiones a PostgreSQL. Este módulo viene del extra `[pool]` de psycopg3, que no estaba declarado en `requirements.txt`.

**Fix**
Agregar el extra `pool` en `requirements.txt`:

```
# ANTES
psycopg[binary]>=3.1,<4

# DESPUÉS
psycopg[binary,pool]>=3.1,<4
```

Tras este cambio hay que reconstruir la imagen:
```bash
docker compose build --no-cache
```

---

## 4. `tryton.cfg` no encontrado — estructura namespace package incorrecta

**Error**
```
FileNotFoundError: /usr/local/lib/python3.12/site-packages/trytond/modules/mi_modulo/tryton.cfg
```

**Causa raíz (importante)**
`trytond.modules` es un paquete regular Python (tiene `__init__.py`), no un namespace package. Cuando pip hace un install editable con la estructura `trytond/modules/mi_modulo/`, crea un finder que intenta hacer `trytond.modules.mi_modulo` importable, pero como `trytond.modules.__path__` solo apunta a `site-packages/trytond/modules/`, Python nunca busca en el directorio local del módulo.

El flujo de `trytond` para encontrar archivos es:
1. Llama a `import_module('mi_modulo')` que usa el entry point del grupo `trytond.modules`
2. El entry point llama a `ep.load()` → `importlib.import_module('trytond.modules.mi_modulo')`
3. Este import falla porque `trytond.modules.__path__` no incluye el directorio local
4. Cae al fallback: busca en `site-packages/trytond/modules/mi_modulo/tryton.cfg` → no existe

**Estructura incorrecta (namespace package — NO funciona con pip editable)**
```
modules/mi_modulo/
├── pyproject.toml
└── trytond/              ← namespace package sin __init__.py
    └── modules/          ← namespace package sin __init__.py
        └── mi_modulo/
            ├── __init__.py
            └── tryton.cfg
```
```toml
# entry point incorrecto para editable install
[project.entry-points."trytond.modules"]
mi_modulo = "trytond.modules.mi_modulo"
```

**Estructura correcta (paquete plano — funciona)**
```
modules/mi_modulo/
├── pyproject.toml
└── mi_modulo/            ← paquete Python top-level
    ├── __init__.py
    ├── tryton.cfg        ← en la misma carpeta que __init__.py
    ├── registro.py
    ├── mi_modulo.xml
    └── view/
        ├── registro_form.xml
        └── registro_list.xml
```
```toml
# entry point correcto
[project.entry-points."trytond.modules"]
mi_modulo = "mi_modulo"
```

**Por qué funciona la estructura plana**
Con `mi_modulo = "mi_modulo"`, `ep.load()` importa el paquete top-level `mi_modulo` directamente. El pip editable install crea un `.pth` o finder simple que sí funciona para paquetes top-level. Luego `os.path.dirname(module.__file__)` apunta a `modules/mi_modulo/mi_modulo/`, que es exactamente donde está `tryton.cfg`.

---

## 5. `'str' object has no attribute 'params'` en `_sql_constraints`

**Error**
```
AttributeError: 'str' object has no attribute 'params'
  File "trytond/backend/postgresql/table.py", line 532, in add_constraint
```

**Causa**
En Tryton 8.0 el formato de `_sql_constraints` cambió. Ya no acepta strings como definición de la constraint. Espera objetos de la clase `Unique` (o `Check`) definida en `trytond.model.modelsql`.

**Fix**

```python
# ANTES (funcionaba en versiones anteriores, roto en 8.0)
cls._sql_constraints = [
    ('codigo_unique', 'UNIQUE(codigo)', 'El código debe ser único.'),
]

# DESPUÉS (correcto para Tryton 8.0)
from trytond.model.modelsql import Unique

@classmethod
def __setup__(cls):
    super().__setup__()
    t = cls.__table__()
    cls._sql_constraints += [
        ('codigo_unique', Unique(t, t.codigo), 'El código debe ser único.'),
    ]
```

Puntos clave:
- Importar `Unique` desde `trytond.model.modelsql` (no desde `sql.constraints`)
- Usar `cls.__table__()` para obtener el objeto tabla
- Usar `+=` en lugar de `=` para no pisar los constraints internos que agrega `super().__setup__()`

---

## 6. `'Char' object has no attribute 'model_name'` en el XML de permisos

**Error**
```
AttributeError: 'Char' object has no attribute 'model_name'
trytond.convert.ParsingError: in record 'mi_modulo.access_registro_admin'
```

**Causa**
En Tryton 8.0, el campo `model` de `ir.model.access` es de tipo `Char` (almacena el nombre del modelo como string). Fue migrado de Many2One a Char en Tryton 7.0. El atributo `search=""` en XML solo funciona en campos Many2One porque necesita `field.model_name` para saber en qué modelo buscar.

**Fix**

```xml
<!-- ANTES (incorrecto — model no es Many2One) -->
<record model="ir.model.access" id="access_registro_admin">
    <field name="model" search="[('model', '=', 'mi_modulo.registro')]"/>
    ...
</record>

<!-- DESPUÉS (correcto — escribir el nombre del modelo directamente) -->
<record model="ir.model.access" id="access_registro_admin">
    <field name="model">mi_modulo.registro</field>
    ...
</record>
```

El campo `group` sí admite `search=""` porque sigue siendo Many2One a `res.group`:
```xml
<field name="group" search="[('name', '=', 'Administration')]"/>
```

---

---

## 7. `client.tryton.org` no existe / `sao@8.0` no existe en npm

**Error**
```
DNS_PROBE_POSSIBLE — client.tryton.org
npm error notarget No matching version found for sao@8.0
```

**Causa**
- `client.tryton.org` nunca existió como dominio público.
- El paquete `sao` en npm es una herramienta de scaffolding sin relación con Tryton.

**Fix**
Descargar el cliente SAO oficial desde el servidor de descargas de Tryton y construirlo con npm + grunt:

```
https://downloads.tryton.org/8.0/tryton-sao-last.tgz
```

El `.tgz` contiene el código fuente. Hay que compilarlo:
```bash
npm install --legacy-peer-deps
npx grunt
```

Tras el build, servir los archivos resultantes con nginx.

---

## 8. SAO muestra "sao is not fully installed" al abrir en el navegador

**Error**
```
sao is not fully installed. Please refer to README
```

**Causa**
El primer `Dockerfile.sao` descargaba el `.tgz` y copiaba los archivos sin compilar directamente a nginx. El paquete contiene fuente, no los archivos compilados listos para el navegador.

**Fix**
Build multi-stage en `Dockerfile.sao`: compilar en imagen node, copiar resultado a nginx:

```dockerfile
FROM node:20-bookworm-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates
WORKDIR /sao
RUN curl -fsSL https://downloads.tryton.org/8.0/tryton-sao-last.tgz | tar -xz --strip-components=1
RUN npm install --legacy-peer-deps
RUN npx grunt

FROM nginx:1.26-bookworm
COPY --from=builder /sao/ /usr/share/nginx/html/
COPY nginx-sao.conf /etc/nginx/conf.d/default.conf
```

---

## 9. `curl: (77) error setting certificate file` al descargar SAO en Docker

**Error**
```
curl: (77) error setting certificate file: /etc/ssl/certs/ca-certificates.crt
```

**Causa**
La imagen `node:20-bookworm-slim` no incluye `ca-certificates`, por lo que curl no puede verificar el certificado SSL de `downloads.tryton.org`.

**Fix**
Instalar `ca-certificates` junto con curl en el `Dockerfile.sao`:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates
```

---

## 10. SAO hace POST a `localhost:8001/rpc/` en lugar de `localhost:8000/rpc/`

**Error en consola del navegador**
```
POST http://localhost:8001/rpc/ 404 (Not Found)
```

**Causa**
SAO asume que el backend de Tryton está en el mismo origen donde él es servido. Como SAO está en `:8001`, intenta conectarse a `:8001/rpc/` en vez de `:8000/rpc/`. No hay forma de configurar la URL del servidor en tiempo de build sin modificar el código fuente.

**Fix**
Configurar nginx como proxy inverso para las rutas de Tryton, de modo que todo vaya al mismo origen:

```nginx
# nginx-sao.conf
location /rpc/ {
    proxy_pass http://tryton:8000/rpc/;
}
location ~ ^/([^/]+)/(rpc|session)/ {
    proxy_pass http://tryton:8000$request_uri;
}
location = /custom.css { return 204; }
location = /custom.js  { return 204; }
location / {
    try_files $uri $uri/ /index.html;
}
```

Con esto el navegador solo habla con `:8001` y nginx reenvía internamente a `tryton:8000`. Sin CORS, sin configuración en SAO.

---

## 11. Tryton devuelve 403 Forbidden en peticiones desde SAO (CORS)

**Error en logs de trytond**
```
werkzeug.exceptions.Forbidden: 403 Forbidden
abort(HTTPStatus.FORBIDDEN)
```

**Causa**
`trytond` bloquea cualquier petición cuyo header `Origin` sea distinto al `Host`. Como SAO estaba en `:8001` y trytond en `:8000`, el origin no coincidía y trytond rechazaba todas las peticiones. El bloqueo ocurre en `wsgi.py` antes de procesar nada.

**Fix**
Agregar `cors =` en la sección `[web]` de `trytond.conf`. En este entorno se genera dinámicamente desde el entrypoint:

```bash
# docker-entrypoint.sh
[web]
listen = 0.0.0.0:${TRYTON_PORT:-8000}
cors = ${TRYTON_CORS_ORIGIN:-http://localhost:8001}
```

```yaml
# compose.yml — pasar la variable al contenedor
environment:
  TRYTON_CORS_ORIGIN: ${TRYTON_CORS_ORIGIN:-http://localhost:8001}
```

**Nota:** Con el proxy nginx (incidencia 10) este error desaparece porque el origen siempre es el mismo. La configuración de CORS queda como respaldo.

---

## 12. `docker compose restart` no aplica cambios de `compose.yml` ni `.env`

**Síntoma**
Se modifica `compose.yml` o `.env`, se hace `docker compose restart servicio`, pero los cambios no se reflejan dentro del contenedor.

**Causa**
`docker compose restart` solo para y arranca el contenedor existente. No lo recrea. Los cambios de variables de entorno, volúmenes o imagen solo se aplican al recrear el contenedor.

**Fix**
```bash
# Recrear el contenedor aplicando todos los cambios
docker compose up -d --force-recreate tryton
```

**Regla:** `restart` = reiniciar el proceso. `up --force-recreate` = recrear el contenedor con la nueva configuración.

---

## 13. `docker-entrypoint.sh` modificado localmente no tiene efecto en el contenedor

**Síntoma**
Se edita `docker-entrypoint.sh` en el host pero el contenedor sigue usando la versión anterior.

**Causa**
El `Dockerfile` copia el script dentro de la imagen con `COPY`. Cambiar el archivo local no afecta a los contenedores ya creados ni a la imagen ya construida.

**Fix**
Montar el script como volumen en `compose.yml` para que siempre use la versión del host:

```yaml
volumes:
  - ./modules:/app/modules
  - ./docker-entrypoint.sh:/usr/local/bin/docker-entrypoint.sh:ro
```

Así cualquier edición al script se aplica con un simple `docker compose up -d --force-recreate tryton`, sin necesidad de rebuild.

---

## 14. `trytond-admin --password` no existe en Tryton 8.0

**Error**
```
trytond-admin: error: unrecognized arguments: admin_secret
```

**Causa**
En Tryton 8.0, `trytond-admin` no acepta la contraseña como argumento posicional ni con `--password`. La contraseña se introduce de forma interactiva.

**Fix**
Usar el flag `-p` con un terminal interactivo:

```bash
docker compose exec -it tryton trytond-admin \
  --config /etc/trytond.conf \
  --database tryton \
  -p
# Introducir la contraseña cuando la pida (dos veces)
```

---

## 15. Login bloqueado por rate limiting — `429 Too Many Requests`

**Error**
```
429 Too Many Requests — This user has exceeded an allotted request count.
```

**Causa**
Tryton registra los intentos de login fallidos en la tabla `res_user_login_attempt`. Tras varios fallos consecutivos bloquea la IP temporalmente devolviendo 429.

**Fix**
Limpiar la tabla directamente en PostgreSQL:

```bash
docker compose exec postgres psql -U tryton -d tryton \
  -c "DELETE FROM res_user_login_attempt;"
```

Después resetear la contraseña si era incorrecta:

```bash
docker compose exec -it tryton trytond-admin \
  --config /etc/trytond.conf \
  --database tryton \
  -p
```

---

## 16. Wizard inicial: "The default language English must be translatable"

**Error**
```
The default language "English" must be translatable.
```

**Causa**
Durante el wizard de configuración inicial, Tryton obliga a que el idioma base (English) esté marcado como traducible, independientemente de qué otros idiomas se seleccionen.

**Fix**
En la pantalla "Configure Languages", marcar **English** además de cualquier otro idioma que se quiera activar. Siempre debe estar seleccionado.

---

## 17. No activar todos los módulos en el wizard inicial

**Síntoma**
El wizard ofrece activar `account`, `account_invoice`, `account_invoice_stock`, `account_product` junto con el resto. Activarlos todos deja el sistema en estado incompleto con errores de configuración.

**Causa**
Los módulos de contabilidad requieren configuración obligatoria posterior (plan contable, año fiscal, empresa) que el wizard no cubre. Sin esa configuración, muchas pantallas quedan bloqueadas.

**Recomendación**
Activar solo los módulos base para empezar:
```
company, currency, country, party, product
```
Agregar `stock`, `sale`, `purchase` en un segundo paso. Los módulos de `account` al final, cuando se necesiten.

---

## Reglas generales extraídas

1. **No mapear el puerto de PostgreSQL al host** si hay un servidor local corriendo. Tryton lo alcanza por red interna de Docker.

2. **Siempre usar `setuptools.build_meta`** como build backend en módulos Tryton.

3. **psycopg necesita el extra `[pool]`** para Tryton 8.0: `psycopg[binary,pool]`.

4. **Estructura de módulo editable: paquete top-level**, no namespace package. Entry point: `mi_modulo = "mi_modulo"`.

5. **`_sql_constraints` en Tryton 8.0** requiere `Unique(table, column)` de `trytond.model.modelsql`, no strings SQL.

6. **`ir.model.access.model` es `Char` desde Tryton 7.0**: valor directo, no `search=""`.

7. **SAO no existe en npm ni en PyPI para 8.0.** Descargar desde `downloads.tryton.org/8.0/tryton-sao-last.tgz` y compilar con `npm install --legacy-peer-deps && npx grunt`.

8. **SAO siempre conecta al mismo origen donde es servido.** Usar nginx como proxy inverso para `/rpc/` y `/<db>/rpc/` en lugar de configurar CORS.

9. **`docker compose restart` no recrea el contenedor.** Para aplicar cambios de `compose.yml` o `.env` usar `docker compose up -d --force-recreate <servicio>`.

10. **Montar `docker-entrypoint.sh` como volumen** para que cambios locales se apliquen sin rebuild: `- ./docker-entrypoint.sh:/usr/local/bin/docker-entrypoint.sh:ro`.

11. **Rate limiting de login:** limpiar con `DELETE FROM res_user_login_attempt;` en psql cuando aparezca 429.

12. **En el wizard inicial**, English siempre debe estar marcado como traducible. No activar módulos de `account` hasta tener configuración contable lista.
