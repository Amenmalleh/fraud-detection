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
EVALUATION_REPORT_PATH = MODELS_DIR / "evaluation_report.txt"
ROC_CURVE_PATH = MODELS_DIR / "roc_curve.png"

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

# XGBoost : params fixes (random_state, eval_metric) + grille explorée par
# GridSearchCV (cf. train.py). n_jobs=1 sur l'estimateur : c'est GridSearchCV
# qui parallelise (n_jobs=-1) en lancant plusieurs combinaisons en meme temps,
# pas l'inverse, sinon on sur-souscrit le CPU (parallelisme imbrique).
XGB_BASE_PARAMS = {
    "random_state": RANDOM_STATE,
    "eval_metric": "auc",
    "n_jobs": 1,
}

XGB_PARAM_GRID = {
    "n_estimators": [100, 200],
    "max_depth": [3, 5],
    "learning_rate": [0.01, 0.1],
}

# --- Colonnes ---
TARGET_COLUMN = "Class"           # 0 = transaction legitime, 1 = fraude
COLUMNS_TO_SCALE = ["Amount", "Time"]  # seules colonnes non normalisees dans le dataset Kaggle

# Ordre exact des colonnes vu par le modele a l'entrainement (= colonnes du CSV
# Kaggle moins "Class"). L'API doit reconstruire ce meme ordre avant de predire,
# sinon le modele lirait par exemple "Amount" a la place de "V3".
FEATURE_COLUMNS = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]
