"""Servicio de PROCESAMIENTO de resultados (Python).

Toma los votos de la cola de Redis y:
  1. guarda el voto vigente de cada votante en PostgreSQL (tabla `votes`);
  2. registra cada evento procesado en MongoDB (colección `events`) como bitácora.
"""
import json
import os
import sys
import time

import psycopg2
import redis
from pymongo import MongoClient

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
PG = dict(
    host=os.getenv("POSTGRES_HOST", "db"),
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    dbname=os.getenv("POSTGRES_DB", "votacion"),
)
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017")
MONGO_DB = os.getenv("MONGO_DB", "votacion")


def log(msg):
    print(msg, flush=True)


def connect_postgres():
    while True:
        try:
            conn = psycopg2.connect(**PG)
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(
                    "CREATE TABLE IF NOT EXISTS votes ("
                    " voter_id VARCHAR(64) PRIMARY KEY,"
                    " vote VARCHAR(64) NOT NULL,"
                    " updated_at TIMESTAMPTZ NOT NULL DEFAULT now())"
                )
            log("Conectado a PostgreSQL")
            return conn
        except psycopg2.OperationalError as exc:
            log(f"Esperando a PostgreSQL... ({exc.__class__.__name__})")
            time.sleep(2)


def connect_mongo():
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=2000)
    while True:
        try:
            client.admin.command("ping")
            log("Conectado a MongoDB")
            return client[MONGO_DB]["events"]
        except Exception as exc:  # noqa: BLE001 - reintentar ante cualquier fallo de conexión
            log(f"Esperando a MongoDB... ({exc.__class__.__name__})")
            time.sleep(2)


def process(conn, events, data):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO votes (voter_id, vote) VALUES (%s, %s) "
            "ON CONFLICT (voter_id) DO UPDATE SET vote = EXCLUDED.vote, updated_at = now()",
            (data["voter_id"], data["vote"]),
        )
    events.insert_one(
        {
            "voter_id": data["voter_id"],
            "vote": data["vote"],
            "received_at": data.get("ts"),
            "processed_at": time.time(),
        }
    )


def main():
    cache = redis.Redis(host=REDIS_HOST, port=6379)
    conn = connect_postgres()
    events = connect_mongo()
    log("Worker listo: esperando votos en Redis")

    while True:
        try:
            item = cache.blpop("votes", timeout=5)
            if item is None:
                continue
            raw = item[1]
            try:
                data = json.loads(raw)
                data["voter_id"], data["vote"]  # valida que existan los campos
            except (ValueError, KeyError, TypeError):
                log("Mensaje inválido descartado")  # no se reencola: evitaría un bucle infinito
                continue
            try:
                process(conn, events, data)
                log(f"Voto procesado: {data['voter_id'][:8]} -> {data['vote']}")
            except Exception as exc:  # noqa: BLE001
                # No perder el voto: se devuelve a la cola y se reconecta.
                log(f"Error procesando voto ({exc.__class__.__name__}); reintentando")
                cache.lpush("votes", raw)
                time.sleep(2)
                conn = connect_postgres()
        except redis.exceptions.RedisError as exc:
            log(f"Redis no disponible ({exc.__class__.__name__}); reintentando")
            time.sleep(2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
