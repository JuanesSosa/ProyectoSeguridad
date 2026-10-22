"""Servicio WEB (Python / Flask).

Muestra la página de votación y envía cada voto a Redis (cola "votes").
El servicio `worker` lo procesa después; este contenedor no habla con las bases
de datos relacionales, solo con Redis.
"""
import json
import os
import socket
import time
import uuid

import redis
from flask import Flask, make_response, render_template, request

OPTION_A = os.getenv("OPTION_A", "Gatos")
OPTION_B = os.getenv("OPTION_B", "Perros")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")  # nombre del servicio en docker-compose

app = Flask(__name__)
# El cliente se conecta de forma perezosa: no falla al arrancar si Redis aún no está listo.
cache = redis.Redis(host=REDIS_HOST, port=6379, socket_connect_timeout=2, socket_timeout=2)


@app.route("/", methods=["GET", "POST"])
def index():
    voter_id = request.cookies.get("voter_id") or uuid.uuid4().hex
    vote = request.cookies.get("vote")
    error = None

    if request.method == "POST":
        choice = request.form.get("vote")
        if choice in (OPTION_A, OPTION_B):
            try:
                cache.rpush(
                    "votes",
                    json.dumps({"voter_id": voter_id, "vote": choice, "ts": time.time()}),
                )
                vote = choice
            except redis.exceptions.RedisError:
                error = "No se pudo registrar el voto (Redis no responde). Intenta de nuevo."

    resp = make_response(
        render_template(
            "index.html",
            option_a=OPTION_A,
            option_b=OPTION_B,
            vote=vote,
            error=error,
            hostname=socket.gethostname(),
        ),
        503 if error else 200,
    )
    resp.set_cookie("voter_id", voter_id)
    if vote:
        resp.set_cookie("vote", vote)
    return resp


@app.route("/healthz")
def healthz():
    try:
        cache.ping()
        return {"status": "ok"}
    except redis.exceptions.RedisError:
        return {"status": "redis-down"}, 503
