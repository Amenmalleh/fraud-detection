"""
Simule un flux de transactions en temps reel : rejoue des lignes aleatoires
du dataset Kaggle contre l'API /predict, une transaction toutes les 2
secondes, comme le ferait un systeme de paiement qui interrogerait l'API
en continu.

Prerequis : l'API doit tourner (docker compose up, ou uvicorn en local).
Usage : python scripts/simulate_transactions.py
"""

import random
import signal
import sys
import time
from pathlib import Path

import pandas as pd
import requests

# Sur Windows, la console utilise par defaut un encodage (cp1252) qui ne
# sait pas afficher les emojis utilises ci-dessous (✅ 🚨 📊) et fait planter
# le script avec un UnicodeEncodeError. On force stdout en UTF-8.
# line_buffering=True : sans ca, la sortie reste bufferisee tant qu'elle
# n'est pas connectee a un vrai terminal (ex: redirigee vers un fichier ou
# un pipe) et les transactions n'apparaissent pas une a une en "temps reel"
# comme prevu, mais par paquets.
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "creditcard.csv"
API_URL = "http://localhost:8000/predict"
INTERVAL_SECONDS = 2

# Le handler met juste ce flag a False ; la boucle principale le relit avant
# chaque iteration. C'est plus propre qu'un Ctrl+C qui interromprait
# brutalement une requete HTTP en plein vol.
running = True


def handle_sigint(signum, frame):
    global running
    running = False


def row_to_payload(row):
    payload = {"Time": float(row["Time"]), "Amount": float(row["Amount"])}
    for i in range(1, 29):
        payload[f"V{i}"] = float(row[f"V{i}"])
    return payload


def main():
    signal.signal(signal.SIGINT, handle_sigint)

    print(f"Chargement de {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    print(f"{len(df)} transactions disponibles. Simulation en cours (Ctrl+C pour arreter)...\n")

    count = 0
    fraud_count = 0

    while running:
        row = df.iloc[random.randrange(len(df))]
        payload = row_to_payload(row)

        try:
            response = requests.post(API_URL, json=payload, timeout=5)
            response.raise_for_status()
            result = response.json()
        except requests.RequestException as exc:
            print(f"❌ Erreur API : {exc}")
            time.sleep(INTERVAL_SECONDS)
            continue

        count += 1
        is_fraud = result["is_fraud"]
        confidence_pct = result["confidence"] * 100

        if is_fraud:
            fraud_count += 1
            print(f"🚨 Transaction #{count} — FRAUDE    (confiance: {confidence_pct:5.1f}%)")
        else:
            print(f"✅ Transaction #{count} — LÉGITIME  (confiance: {confidence_pct:5.1f}%)")

        if count % 10 == 0:
            fraud_rate = fraud_count / count * 100
            print(f"📊 Stats : {fraud_count} fraudes / {count} transactions ({fraud_rate:.1f}%)\n")

        time.sleep(INTERVAL_SECONDS)

    print(f"\nArret demande. Total : {fraud_count} fraudes / {count} transactions.")


if __name__ == "__main__":
    main()
