"""
Logique de prediction, isolee dans sa propre classe pour ne pas melanger
"charger/appeler le modele" avec "definir les routes HTTP" (api/main.py).
"""

import os

import joblib
import pandas as pd
from dotenv import load_dotenv

from src.config import COLUMNS_TO_SCALE, FEATURE_COLUMNS, MODEL_PATH, SCALER_PATH

load_dotenv()

DEFAULT_THRESHOLD = 0.5


class FraudPredictor:
    """
    Charge le modele et le scaler UNE SEULE FOIS a l'instanciation (pas a
    chaque requete : relire un .pkl depuis le disque a chaque appel serait
    beaucoup trop lent pour une API), puis reutilise ces objets en memoire
    pour toutes les predictions suivantes.
    """

    def __init__(self, model_path=None, scaler_path=None, threshold=DEFAULT_THRESHOLD):
        model_path = model_path or os.getenv("MODEL_PATH", str(MODEL_PATH))
        scaler_path = scaler_path or os.getenv("SCALER_PATH", str(SCALER_PATH))

        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        self.threshold = threshold  # proba >= threshold => classee comme fraude

    def predict(self, transaction_data: dict) -> tuple[bool, float]:
        """
        transaction_data : dict avec les cles Time, V1..V28, Amount.
        Retourne (is_fraud, confidence) ou confidence est la probabilite de
        fraude (entre 0 et 1) donnee par le modele.
        """
        # On reordonne les colonnes pour matcher exactement l'ordre utilise a
        # l'entrainement (Time, V1..V28, Amount). Un DataFrame construit a partir
        # d'un dict n'a aucune garantie d'ordre une fois les cles melangees.
        df = pd.DataFrame([transaction_data])[FEATURE_COLUMNS]

        # Meme transformation que pendant l'entrainement, avec le scaler DEJA
        # entraine (on ne fait jamais de fit() ici, seulement transform()).
        df[COLUMNS_TO_SCALE] = self.scaler.transform(df[COLUMNS_TO_SCALE])

        confidence = float(self.model.predict_proba(df)[0, 1])
        is_fraud = confidence >= self.threshold

        return is_fraud, confidence
