#!/bin/bash
# Guide de demarrage du projet Fraud Detection (Linux/macOS/Git Bash).
# Verifie les prerequis dans l'ordre, puis lance toute la stack Docker.
set -e

cd "$(dirname "$0")/.."

echo "=== Fraud Detection - Setup ==="
echo ""

# 1. Le dataset doit etre present avant toute chose : sans lui, l'entrainement
#    (etape 3) ne peut pas tourner.
if [ ! -f "data/creditcard.csv" ]; then
  echo "❌ data/creditcard.csv introuvable."
  echo "   Telecharge le dataset Kaggle 'Credit Card Fraud Detection' et place-le dans data/."
  exit 1
fi
echo "✅ data/creditcard.csv trouve"

# 2. "docker info" echoue si le daemon Docker ne tourne pas (Docker Desktop
#    pas demarre), independamment du fait que la commande "docker" existe.
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker ne repond pas. Demarre Docker Desktop puis relance ce script."
  exit 1
fi
echo "✅ Docker est demarre"

# docker-compose (v1, binaire separe) ou docker compose (v2, plugin integre) :
# on utilise celui qui est disponible plutot que d'en imposer un seul.
if command -v docker-compose > /dev/null 2>&1; then
  COMPOSE_CMD="docker-compose"
else
  COMPOSE_CMD="docker compose"
fi

# 3. Le modele n'est jamais commite (trop lourd pour Git, cf. .gitignore) :
#    on l'entraine automatiquement s'il manque, pour que ce script marche
#    meme sur une machine qui clone le repo pour la premiere fois.
if [ ! -f "models/fraud_model.pkl" ] || [ ! -f "models/scaler.pkl" ]; then
  echo "⚠️  Modele introuvable, entrainement en cours (python -m src.train)..."
  # "-m" est necessaire (pas "python src/train.py") : train.py utilise des
  # imports de paquet ("from src.config import ..."), qui ne fonctionnent
  # que si Python est lance depuis la racine du projet avec -m.
  python -m src.train
else
  echo "✅ Modele deja entraine (models/fraud_model.pkl)"
fi

# 4. Build + lancement des 3 services en arriere-plan.
echo ""
echo "🚀 Lancement de $COMPOSE_CMD up --build..."
$COMPOSE_CMD up --build -d

# 5. db et api ont un healthcheck explicite (docker-compose.yml) ; dashboard
#    n'en a pas (nginx demarre quasi instantanement), on verifie juste qu'il
#    tourne.
wait_for_healthy() {
  local name=$1
  echo -n "   $name : "
  for _ in $(seq 1 30); do
    status=$(docker inspect --format='{{.State.Health.Status}}' "$name" 2>/dev/null || echo "")
    if [ "$status" = "healthy" ]; then
      echo "healthy"
      return 0
    fi
    sleep 2
  done
  echo "timeout (verifie avec '$COMPOSE_CMD logs $name')"
  return 1
}

echo "⏳ Attente que les services soient prets..."
wait_for_healthy fraud_db
wait_for_healthy fraud_api

echo -n "   fraud_dashboard : "
for _ in $(seq 1 15); do
  status=$(docker inspect --format='{{.State.Status}}' fraud_dashboard 2>/dev/null || echo "")
  if [ "$status" = "running" ]; then
    echo "running"
    break
  fi
  sleep 2
done

echo ""
echo "✅ Systeme disponible sur http://localhost:3000"
