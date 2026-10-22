# Proyecto 03 – Aplicación multicontenedor con Docker Compose

Infraestructura y Seguridad Computacional · Universidad de Ibagué · Grupo 02 – 2026B

Aplicación de votación ("Gatos vs Perros") formada por **6 contenedores** que se comunican entre sí y se
levantan con un solo comando.

```
 Navegador ──► vote (Python/Flask) ──► redis ──► worker (Python) ──┬─► db (PostgreSQL)
                                                                    └─► mongo (MongoDB)
 Navegador ──► result (Node.js/Express) ◄── lee de db (PostgreSQL) y mongo (MongoDB)
```

| Servicio | Tecnología | Rol según el instructivo | Puerto en tu equipo |
|---|---|---|---|
| `vote` | Python (Flask + gunicorn) | Contenedor **web** | `5000` |
| `result` | Node.js (Express) | Contenedor para **visualizar resultados** | `5001` |
| `worker` | Python | Contenedor de **procesamiento de resultados** | – (solo red interna) |
| `redis` | Redis 7 | Base de datos (cola de votos) | – |
| `db` | PostgreSQL 16 | Base de datos relacional (voto vigente por votante) | – |
| `mongo` | MongoDB 7 | Base de datos de documentos (bitácora de eventos) | – |

Flujo: el usuario vota en `vote` → el voto entra a una cola en `redis` → `worker` lo toma, lo guarda en
`db` (PostgreSQL) y registra el evento en `mongo` → `result` consulta ambas bases y lo muestra.

---

## 1. Requisitos

- Linux con Docker Engine y el plugin Compose v2 (`docker --version`, `docker compose version`).
- Cuenta en Docker Hub y en GitHub.

## 2. Ejecutar la aplicación

```bash
cp .env.example .env        # edita DOCKERHUB_USER y la contraseña de PostgreSQL
docker compose up -d --build
docker compose ps           # los 6 servicios deben quedar "running" / "healthy"
```

- Votar: <http://localhost:5000>
- Ver resultados: <http://localhost:5001>

Para generar votos desde la terminal (cada `voter_id` cuenta como un votante distinto):

```bash
for i in 1 2 3 4 5; do curl -s -o /dev/null -X POST -d "vote=Gatos"  -b "voter_id=user$i" localhost:5000; done
for i in 6 7;       do curl -s -o /dev/null -X POST -d "vote=Perros" -b "voter_id=user$i" localhost:5000; done
```

Para apagarla: `docker compose down` (conserva los volúmenes) o `docker compose down -v` (los borra).

## 3. Explicación secuencial del `docker-compose.yml`

El archivo se lee de arriba hacia abajo; cada bloque corresponde a un criterio de la rúbrica.

**Paso 1 – Archivo y formato (criterio 1).** El archivo se llama `docker-compose.yml`, está en YAML (la
indentación con espacios es parte de la sintaxis) y tiene tres secciones de primer nivel: `services`,
`volumes` y `networks`.

**Paso 2 – Servicios (criterio 2).** Cada entrada bajo `services:` es un contenedor.
- `vote`, `result` y `worker` usan `build:` (construyen su imagen con el `Dockerfile` de su carpeta) e
  `image:` (el nombre con el que esa imagen se publica en Docker Hub).
- `redis`, `db` y `mongo` usan imágenes oficiales (`image:`) sin construir nada.

**Paso 3 – Enlaces entre servicios (criterio 3).** Hay dos mecanismos:
- *Resolución por nombre:* dentro de una red de Compose cada servicio es accesible por su nombre. Por eso
  `vote` usa `REDIS_HOST: redis`, `worker` usa `POSTGRES_HOST: db` y `MONGO_URL: mongodb://mongo:27017`.
- *Orden de arranque:* `depends_on` con `condition: service_healthy` hace que un servicio espere a que sus
  dependencias pasen su `healthcheck`. Así `worker` no arranca hasta que Redis, PostgreSQL y MongoDB responden.

**Paso 4 – Volúmenes (criterio 4).** Los contenedores son efímeros; los volúmenes guardan los datos.
Hay tres volúmenes con nombre, declarados en la sección `volumes:` y montados en cada base de datos:
`redis-data` → `/data`, `db-data` → `/var/lib/postgresql/data`, `mongo-data` → `/data/db`.
Prueba: `docker compose down && docker compose up -d` y los votos siguen ahí.

**Paso 5 – Puertos (criterio 5).** `ports: "5000:80"` publica el puerto 80 del contenedor `vote` en el
5000 de tu equipo (formato `host:contenedor`); `result` hace lo mismo con `5001:80`. Las bases de datos
y el worker **no publican puertos**: solo se alcanzan desde la red interna.

**Paso 6 – Redes (criterio 6).** Dos redes `bridge`:
- `front-tier`: la usan `vote` y `result`, que son los que alcanza el usuario.
- `back-tier`: conecta todos los servicios con las bases de datos. `redis`, `db`, `mongo` y `worker`
  están *solo* aquí, aislados del exterior.

## 4. Verificación rápida

```bash
docker compose ps                                   # estado y healthchecks
docker compose logs -f worker                       # "Voto procesado: ..."
docker compose exec db psql -U postgres -d votacion -c "SELECT vote, COUNT(*) FROM votes GROUP BY vote;"
docker compose exec mongo mongosh votacion --quiet --eval "db.events.find().sort({processed_at:-1}).limit(3)"
docker network ls | grep p03                        # las dos redes
docker volume ls   | grep p03                       # los tres volúmenes
```

## 5. Publicar en Docker Hub (criterio 7)

```bash
docker login                                         # usuario y contraseña (o token) de Docker Hub
docker compose build
docker compose push vote result worker               # sube las 3 imágenes propias
```

Quedan en `https://hub.docker.com/r/<TU_USUARIO>/proyecto03-vote`, `...-result` y `...-worker`.
Comprobación desde cualquier equipo: `docker pull <TU_USUARIO>/proyecto03-vote:1.0`.

## 6. Publicar en GitHub (criterio 7)

```bash
git init
git add .
git status                                           # verifica que .env NO aparezca
git commit -m "Proyecto 03: aplicación multicontenedor con Docker Compose"
git branch -M main
git remote add origin https://github.com/<TU_USUARIO>/proyecto03-multicontenedor.git
git push -u origin main
```

El repositorio debe ser **público** y contener `docker-compose.yml`, las carpetas `vote/`, `worker/` y
`result/`, `.env.example` y este README.

## 7. Consideraciones de seguridad

- Las contraseñas no están escritas en el compose: se leen de `.env`, que está en `.gitignore`.
  El valor por defecto (`postgres`) existe solo para que el compose valide; cámbialo en tu `.env`.
- Bases de datos y worker sin puertos publicados + redes separadas = menor superficie de ataque.
- Imágenes con versión fija (`redis:7-alpine`, `postgres:16-alpine`, `mongo:7`) en lugar de `latest`.
- Dependencias de Python y Node auditadas (`pip-audit` y `npm audit`) sin vulnerabilidades conocidas
  al momento de la entrega.
- MongoDB corre sin autenticación porque solo es accesible desde `back-tier`; en producción debería
  activarse (usuario y contraseña) y cifrarse el tráfico.

## 8. Qué se entrega en Moodle (hasta el domingo 25/oct/2026, 23:59)

1. Archivo de texto con el enlace de GitHub del proyecto y los enlaces de Docker Hub (ver `enlaces.txt`).
2. Video en formato **MP4** donde participen todos los integrantes (ver `GUION_VIDEO.md`).

## Referencias

- Docker Inc. *Compose file reference*. <https://docs.docker.com/reference/compose-file/>
- Docker Inc. *Docker Compose overview*. <https://docs.docker.com/compose/>
- Docker Inc. *Docker Hub – repositories*. <https://docs.docker.com/docker-hub/>
- La arquitectura (web → Redis → worker → base de datos → visualización) se inspira en el ejemplo
  público `dockersamples/example-voting-app`; el código de este proyecto es propio.
