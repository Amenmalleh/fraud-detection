# Fraud Detection

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-Random%20Forest-F7931E?logo=scikitlearn&logoColor=white)

Détecte les transactions bancaires frauduleuses en temps réel : un modèle Random Forest entraîné sur le dataset Kaggle *Credit Card Fraud Detection* (AUC-ROC = 0.9836), exposé via une API FastAPI et visualisé dans un dashboard React. Toute la stack (API + base + dashboard) se lance avec une seule commande Docker.

## Architecture

```
Pipeline ML (local, une seule fois, avant Docker) :

  data/creditcard.csv -> src/preprocessing.py -> src/train.py -> models/*.pkl

Stack applicative (docker compose up --build) :

┌──────────────────────────────────────────────────────────────────────────┐
│                          docker-compose.yml                              │
│                                                                          │
│   ┌─────────────┐        ┌─────────────┐        ┌─────────────┐        │
│   │  dashboard  │  /api  │     api     │  SQL   │      db     │        │
│   │ React+Nginx │ ─────▶ │   FastAPI   │ ─────▶ │ PostgreSQL  │        │
│   │   :3000     │        │    :8000    │        │   :5432     │        │
│   └─────────────┘        └──────┬──────┘        └─────────────┘        │
│                                  │ lit (volume read-only)               │
│                                  ▼                                      │
│                           ┌─────────────┐                              │
│                           │  models/    │                              │
│                           │  *.pkl      │                              │
│                           └─────────────┘                              │
└──────────────────────────────────────────────────────────────────────────┘
```

## Structure du projet

```
fraud-detection/
├── data/                 # creditcard.csv (non commite, voir Prerequis)
├── notebooks/
│   └── 01_eda.ipynb      # exploration des donnees
├── src/                  # pipeline ML
│   ├── config.py
│   ├── preprocessing.py
│   └── train.py
├── api/                  # API FastAPI
│   ├── main.py
│   ├── predictor.py
│   ├── database.py
│   ├── schemas.py
│   ├── Dockerfile
│   └── tests/
├── dashboard/            # dashboard React + Vite
│   ├── src/
│   ├── Dockerfile
│   └── nginx.conf
├── models/               # fraud_model.pkl + scaler.pkl (generes localement)
├── scripts/
│   ├── setup.sh          # demarrage guide (Linux/macOS)
│   ├── setup.ps1         # demarrage guide (Windows PowerShell)
│   └── test_api.sh       # tests des endpoints
├── docker-compose.yml
└── requirements.txt
```

## Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) démarré
- Python 3.11+ (pour entraîner le modèle ; l'image Docker de l'API utilise aussi 3.11)
- Le dataset Kaggle [Credit Card Fraud Detection](https://www.kaggle.com/mlg-ulb/creditcardfraud), à placer dans `data/creditcard.csv` (non fourni dans le repo : 144 Mo, données sensibles, cf. `.gitignore`)

## Démarrage

```bash
git clone <url-du-repo>
python -m venv venv && source venv/Scripts/activate && pip install -r requirements.txt
python -m src.train
docker compose up --build
```

> Note : la consigne historique du projet mentionnait `python src/train.py`, mais
> cette commande échoue (`ModuleNotFoundError: No module named 'src'`) car
> `train.py` importe `src.config` comme un paquet. `python -m src.train` est la
> forme correcte — c'est ce qu'utilisent `scripts/setup.sh` et `scripts/setup.ps1`.

Ou plus simplement, en laissant le script tout faire (verifie les prerequis, entraine le modele si besoin, lance Docker) :

```bash
./scripts/setup.sh        # Linux / macOS / Git Bash
./scripts/setup.ps1        # Windows PowerShell
```

Une fois démarré : **http://localhost:3000** (dashboard).

## Endpoints API

| Méthode | Route | Description |
|---|---|---|
| GET | `/health` | Vérifie que l'API et le modèle sont chargés |
| POST | `/predict` | Analyse une transaction et la logge en base |
| GET | `/stats` | Statistiques globales (total, taux de fraude...) |
| GET | `/transactions?limit=50` | Dernières transactions loggées |

```bash
curl http://localhost:8000/health
# {"status":"ok","model_loaded":true}

curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"Amount": 50.0, "Time": 10000.0}'
# {"is_fraud":false,"confidence":0.027,"transaction_id":"1","timestamp":"..."}

curl http://localhost:8000/stats
# {"total_transactions":1,"total_fraud":0,"fraud_rate":0.0,"avg_confidence":0.027}
```

Tester tous les endpoints d'un coup :

```bash
./scripts/test_api.sh
```

## Résultats du modèle

Random Forest retenu face à XGBoost (`src/train.py` entraîne les deux et garde le meilleur) :

| Modèle | AUC-ROC |
|---|---|
| **Random Forest** ✅ | **0.9836** |
| XGBoost | 0.9745 |

Features les plus importantes : `V14`, `V10`, `V4`, `V12`, `V17`.

## Pourquoi ces choix techniques ?

- **AUC-ROC plutôt que l'accuracy** : le dataset est très déséquilibré
  (~0.17% de fraudes). Un modèle qui prédit toujours "légitime" aurait
  99.8% d'accuracy sans jamais détecter de fraude. L'AUC-ROC mesure la
  capacité du modèle à séparer les deux classes, peu importe le déséquilibre.
- **SMOTE** : crée des exemples synthétiques de fraude pour équilibrer le
  train set, appliqué uniquement sur le train (jamais sur le test) pour
  garder une évaluation réaliste.
- **StandardScaler sur Amount/Time seulement** : les colonnes V1..V28 sont
  déjà issues d'une transformation PCA et sont sur une échelle comparable ;
  seules Amount et Time sont dans leurs unités brutes.
- **Multi-stage Docker (api/ et dashboard/)** : le stage de build (pip install /
  npm ci + npm run build) n'est jamais copié dans l'image finale — seuls les
  fichiers nécessaires à l'exécution le sont, pour des images plus légères.
- **Contexte de build = racine pour l'API** : `api/Dockerfile` copie aussi
  `src/`, car `api/predictor.py` réutilise `src/config.py` (mêmes constantes
  que pendant l'entraînement). Le `Dockerfile` reste dans `api/` pour
  l'organisation, mais `docker-compose.yml` le construit avec `context: .`.
- **Volume `./models:/app/models:ro`** : permet de ré-entraîner le modèle sur
  la machine hôte et de relancer juste le conteneur API, sans reconstruire
  l'image ; `:ro` (read-only) empêche le conteneur de modifier le modèle.
