// Servicio para VISUALIZAR resultados (Node.js / Express).
// Lee los conteos desde PostgreSQL y la bitácora de eventos desde MongoDB.
const express = require("express");
const { Pool } = require("pg");
const { MongoClient } = require("mongodb");

const PORT = 80;
const OPTION_A = process.env.OPTION_A || "Gatos";
const OPTION_B = process.env.OPTION_B || "Perros";

const pool = new Pool({
  host: process.env.POSTGRES_HOST || "db", // nombre del servicio en docker-compose
  user: process.env.POSTGRES_USER || "postgres",
  password: process.env.POSTGRES_PASSWORD || "postgres",
  database: process.env.POSTGRES_DB || "votacion",
  port: 5432,
});
pool.on("error", (err) => console.error("Error en el pool de PostgreSQL:", err.message));

const mongo = new MongoClient(process.env.MONGO_URL || "mongodb://mongo:27017", {
  serverSelectionTimeoutMS: 2000,
});
const MONGO_DB = process.env.MONGO_DB || "votacion";

const app = express();
app.use(express.static("public"));

app.get("/api/results", async (_req, res) => {
  const out = { options: [OPTION_A, OPTION_B], counts: {}, events: [], errors: [] };

  try {
    const { rows } = await pool.query("SELECT vote, COUNT(*)::int AS count FROM votes GROUP BY vote");
    for (const r of rows) out.counts[r.vote] = r.count;
  } catch (err) {
    // La tabla aún no existe hasta que el worker procese el primer voto.
    out.errors.push("postgres: " + err.message);
  }

  try {
    const docs = await mongo
      .db(MONGO_DB)
      .collection("events")
      .find({}, { projection: { _id: 0 } })
      .sort({ processed_at: -1 })
      .limit(5)
      .toArray();
    out.events = docs;
  } catch (err) {
    out.errors.push("mongo: " + err.message);
  }

  res.json(out);
});

app.get("/healthz", (_req, res) => res.json({ status: "ok" }));

app.listen(PORT, () => console.log(`Resultados escuchando en el puerto ${PORT}`));
