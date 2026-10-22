# Guion del video (MP4) – Proyecto 03

**Duración sugerida:** 10–12 minutos. **Regla de la rúbrica:** deben aparecer y hablar **todos** los
integrantes (hasta 5). Graba la pantalla con la terminal y el editor abiertos (OBS, la grabadora de
Windows con `Win+G`, o la de la VM). Antes de grabar: `docker compose down -v` para empezar limpio.

Reparte las partes así (si son menos de 5, junta partes):

| # | Quién | Min. | Qué muestra y dice | Criterio |
|---|---|---|---|---|
| 1 | Integrante 1 | 1 | Presentación del grupo y de la app: diagrama del README (vote → redis → worker → db/mongo, y result). Qué hace cada contenedor. | – |
| 2 | Integrante 2 | 2.5 | Abrir `docker-compose.yml`. **Servicios**: `build` vs `image`, los 6 servicios. **Enlaces**: nombres de servicio (`REDIS_HOST: redis`) y `depends_on` con `service_healthy`. | 1, 2, 3 |
| 3 | Integrante 3 | 2 | **Volúmenes** (3, uno por base de datos), **puertos** (`5000:80`, `5001:80`, y por qué las BD no publican puertos) y **redes** (`front-tier` / `back-tier`). | 4, 5, 6 |
| 4 | Integrante 4 | 3 | Demo: `docker compose up -d --build`, `docker compose ps`, votar en `localhost:5000`, ver `localhost:5001`, `docker compose logs worker`, consulta a PostgreSQL y a MongoDB (comandos del README §4). Probar persistencia: `down` y `up` sin `-v`. | 2–6 |
| 5 | Integrante 5 | 2.5 | **Publicación**: `docker login`, `docker compose build`, `docker compose push vote result worker`; mostrar las 3 imágenes en Docker Hub; `git push` y mostrar el repositorio en GitHub (sin `.env`). | 7 |
| – | Todos | 0.5 | Cierre: cada uno dice su nombre y una frase de lo que aportó. | Trabajo en equipo |

## Consejos

- Habla con tus palabras; no leas el README de corrido (el instructivo pide evitar copiar y pegar).
- Ten el `docker login` hecho antes de grabar y **no muestres contraseñas ni tokens** en pantalla.
- Si algo falla en vivo, déjalo: explicar cómo lo resolvieron suma en "solución de conflictos".
- Exporta en **MP4** y confirma que se escucha el audio de todos antes de subirlo a Moodle.
