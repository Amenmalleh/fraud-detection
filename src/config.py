"""
Configuration centrale du projet : chemins, hyperparametres, noms de colonnes.

Pourquoi un fichier config a part ?
Pour eviter de repeter les memes chemins/valeurs dans preprocessing.py et train.py.
Si on change un chemin ou un hyperparametre, on le change a un seul endroit.
"""

from pathlib import Path

# --- Chemins ---
# Path(__file__).parent remonte du fichier config.py jusqu'au dossier src/,
# puis .parent remonte encore jusqu'a la racine du projet fraud-detection/.
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

# Le dataset est deja copie dans data/creditcard.csv (cf. dossier data/ du projet).
KAGGLE_DATASET_PATH = DATA_DIR / "creditcard.csv"

MODEL_PATH = MODELS_DIR / "fraud_model.pkl"
SCALER_PATH = MODELS_DIR / "scaler.pkl"

# --- Hyperparametres ---
RANDOM_STATE = 42      # fixe la graine aleatoire : resultats reproductibles a chaque execution
TEST_SIZE = 0.2        # 20% des donnees pour le test, 80% pour l'entrainement

# Random Forest
RF_PARAMS = {
    "n_estimators": 100,
    "max_depth": 10,
    "random_state": RANDOM_STATE,
    "n_jobs": -1,       # utilise tous les coeurs CPU disponibles
}

# XGBoost
XGB_PARAMS = {
    "n_estimators": 100,
    "max_depth": 6,
    "learning_rate": 0.1,
    "random_state": RANDOM_STATE,
    "eval_metric": "auc",
}

# --- Colonnes ---
TARGET_COLUMN = "Class"           # 0 = transaction legitime, 1 = fraude
COLUMNS_TO_SCALE = ["Amount", "Time"]  # seules colonnes non normalisees dans le dataset Kaggle

# Ordre exact des colonnes vu par le modele a l'entrainement (= colonnes du CSV
# Kaggle moins "Class"). L'API doit reconstruire ce meme ordre avant de predire,
# sinon le modele lirait par exemple "Amount" a la place de "V3".
FEATURE_COLUMNS = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]
