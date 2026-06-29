"""
Verifie que les composants critiques du systeme sont operationnels : modele,
scaler, API (sante, predict, explain, stats) et dashboard.

Lance l'API (et le dashboard si tu veux le check complet) avant d'executer
ce script. Usage : python scripts/health_check.py
"""

import sys
from pathlib import Path

import joblib
import requests

# Sur Windows, la console utilise par defaut un encodage (cp1252) qui ne
# sait pas afficher les emojis ✅/❌ utilises ci-dessous et fait planter le
# script avec un UnicodeEncodeError. On force stdout en UTF-8, qui sait
# tout afficher, sur toutes les plateformes.
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "fraud_model.pkl"
SCALER_PATH = BASE_DIR / "models" / "scaler.pkl"

API_URL = "http://localhost:8000"
DASHBOARD_URL = "http://localhost:3000"

results = []


def check(description, condition):
    icon = "✅" if condition else "❌"
    print(f"{icon} {description}")
    results.append(condition)


def main():
    print("=== Health Check - Fraud Detection System ===\n")

    # 1-2. Le modele et le scaler doivent exister sur le disque ET pouvoir
    # etre deserialises (un fichier .pkl corrompu existerait mais echouerait
    # au chargement).
    try:
        joblib.load(MODEL_PATH)
        check("fraud_model.pkl existe et est chargeable", True)
    except Exception:
        check("fraud_model.pkl existe et est chargeable", False)

    try:
        joblib.load(SCALER_PATH)
        check("scaler.pkl existe et est chargeable", True)
    except Exception:
        check("scaler.pkl existe et est chargeable", False)

    # 3. /health
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        check("API repond sur GET /health", response.status_code == 200 and response.json().get("status") == "ok")
    except requests.RequestException:
        check("API repond sur GET /health", False)

    # 4. /predict : on verifie juste la presence des cles attendues dans la reponse.
    try:
        response = requests.post(f"{API_URL}/predict", json={"Amount": 50.0, "Time": 10000.0}, timeout=5)
        body = response.json()
        expected_keys = {"is_fraud", "confidence", "transaction_id", "timestamp"}
        check("/predict retourne le bon format JSON", response.status_code == 200 and expected_keys <= body.keys())
    except requests.RequestException:
        check("/predict retourne le bon format JSON", False)

    # 5. /explain
    try:
        response = requests.post(f"{API_URL}/explain", json={"Amount": 50.0, "Time": 10000.0}, timeout=5)
        body = response.json()
        check("/explain retourne 5 features", response.status_code == 200 and len(body.get("explanation", [])) == 5)
    except requests.RequestException:
        check("/explain retourne 5 features", False)

    # 6. Base de donnees, verifiee indirectement : /stats interroge PostgreSQL,
    # donc si elle repond, la connexion DB fonctionne.
    try:
        response = requests.get(f"{API_URL}/stats", timeout=5)
        check("Base de donnees accessible (GET /stats repond)", response.status_code == 200)
    except requests.RequestException:
        check("Base de donnees accessible (GET /stats repond)", False)

    # 7. Dashboard
    try:
        response = requests.get(DASHBOARD_URL, timeout=5)
        check("Dashboard accessible sur localhost:3000", response.status_code == 200)
    except requests.RequestException:
        check("Dashboard accessible sur localhost:3000", False)

    passed = sum(results)
    total = len(results)
    print(f"\nSysteme operationnel : {passed}/{total} checks passes")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
