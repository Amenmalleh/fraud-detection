/*
 * Toutes les fonctions d'appel a l'API sont regroupees ici, pour ne pas
 * eparpiller des `axios.get(...)` dans chaque composant. Si l'URL ou le
 * client HTTP change un jour, on ne modifie qu'un seul fichier.
 */
import axios from "axios";

// baseURL = "/api" : ces requetes sont interceptees par le proxy Vite
// (vite.config.js) qui les redirige vers FastAPI (localhost:8000) en
// retirant le prefixe "/api". Cela evite tout probleme de CORS en dev.
const client = axios.create({
  baseURL: "/api",
  timeout: 5000,
});

export async function fetchStats() {
  const { data } = await client.get("/stats");
  return data;
}

export async function fetchTransactions(limit = 50) {
  const { data } = await client.get("/transactions", { params: { limit } });
  return data;
}

export async function predictTransaction(transaction) {
  const { data } = await client.post("/predict", transaction);
  return data;
}

export async function explainTransaction(transaction) {
  const { data } = await client.post("/explain", transaction);
  return data;
}

export async function fetchHealth() {
  const { data } = await client.get("/health");
  return data;
}
