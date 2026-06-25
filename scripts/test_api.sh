#!/bin/bash
# Teste les 5 endpoints de l'API contre un serveur deja demarre
# (docker compose up, ou "uvicorn api.main:app" en local).
#
# Usage : ./scripts/test_api.sh [URL_DE_BASE]
# Par defaut : http://localhost:8000

BASE_URL="${1:-http://localhost:8000}"
PASS=0
FAIL=0

check() {
  local description="$1"
  local ok="$2"
  if [ "$ok" = "true" ]; then
    echo "✅ $description"
    PASS=$((PASS + 1))
  else
    echo "❌ $description"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== Test de l'API Fraud Detection ($BASE_URL) ==="
echo ""

# 1. /health
health=$(curl -s "$BASE_URL/health")
if echo "$health" | grep -q '"status":"ok"'; then
  check "GET /health -> status: ok" true
else
  check "GET /health -> status: ok" false
fi

# 2. /predict avec une transaction normale (petit montant, features par defaut)
normal=$(curl -s -X POST "$BASE_URL/predict" \
  -H "Content-Type: application/json" \
  -d '{"Amount": 50.0, "Time": 10000.0}')
if echo "$normal" | grep -q '"is_fraud":false'; then
  check "POST /predict (transaction normale) -> is_fraud: false" true
else
  check "POST /predict (transaction normale) -> is_fraud: false" false
fi

# 3. /predict avec une transaction suspecte (montant eleve + features extremes,
#    cf. api/tests/test_api.py pour le meme scenario)
suspect=$(curl -s -X POST "$BASE_URL/predict" \
  -H "Content-Type: application/json" \
  -d '{"Amount": 15000.0, "Time": 50000.0, "V1": -8.0, "V2": 7.5, "V3": -9.0, "V4": 6.5, "V10": -7.0, "V12": -8.5, "V14": -9.5, "V17": -6.0}')
if echo "$suspect" | grep -q '"is_fraud":true'; then
  check "POST /predict (transaction suspecte) -> is_fraud: true" true
else
  check "POST /predict (transaction suspecte) -> is_fraud: true" false
fi

# 4. /stats : on verifie juste la presence des cles attendues, pas leurs valeurs
#    (qui dependent de l'historique deja en base).
stats=$(curl -s "$BASE_URL/stats")
if echo "$stats" | grep -q '"total_transactions"' && echo "$stats" | grep -q '"fraud_rate"'; then
  check "GET /stats -> structure JSON valide" true
else
  check "GET /stats -> structure JSON valide" false
fi

# 5. /transactions : doit renvoyer une liste non vide puisque les 2 appels
#    /predict ci-dessus viennent d'en logger au moins une.
transactions=$(curl -s "$BASE_URL/transactions?limit=50")
if [ -n "$transactions" ] && [ "$transactions" != "[]" ]; then
  check "GET /transactions -> liste non vide" true
else
  check "GET /transactions -> liste non vide" false
fi

echo ""
echo "Résultat : $PASS réussis, $FAIL échoués"
[ "$FAIL" -eq 0 ]
