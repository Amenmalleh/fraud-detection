# Fraud Detection

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-tuned-EC0000?logo=numpy&logoColor=white)
![AUC-ROC](https://img.shields.io/badge/AUC--ROC-0.9836-brightgreen)

## Le projet

Détecte les transactions bancaires frauduleuses en temps réel à partir de leurs seules caractéristiques numériques, sans connaître l'identité du porteur ni le commerçant. Le modèle (Random Forest, AUC-ROC 0.9836) tourne derrière une API qui répond en ~25-50ms, avec un dashboard de monitoring et une explication de chaque décision. Pensé comme un système qu'une équipe fraude pourrait brancher sur un flux de paiement réel, pas comme un notebook isolé.

## Architecture

```
┌─────────────────────────────── Couche ML (src/) ───────────────────────────────┐
│                                                                                  │
│  data/creditcard.csv → preprocessing.py (SMOTE, scaling) → train.py            │
│                                  │                                              │
│                                  ├─ Random Forest (params fixes)                │
│                                  └─ XGBoost (GridSearchCV : 8 combos x cv=3)    │
│                                  │                                              │
│                                  ▼                                              │
│              models/fraud_model.pkl + scaler.pkl + evaluation_report.txt       │
│                              + roc_curve.png                                    │
└──────────────────────────────────┬───────────────────────────────────────────-─┘
                                    │ chargé une fois au demarrage
┌───────────────────────────────────┴──────────────────────────────────────────┐
│                          Couche API (api/) — FastAPI                        │
│                                                                                │
│   GET /health   POST /predict   POST /explain   GET /stats   GET /transactions│
│                                    │                                          │
│                                    ▼                                         │
│                          PostgreSQL (transactions loggees)                   │
└────────────────────────────────────┬──────────────────────────────────────--─┘
                                     │ /api/* (proxy nginx en prod, proxy Vite en dev)
┌────────────────────────────────────┴──────────────────────────────────────---┐
│                    Couche Dashboard (dashboard/) — React + Vite             │
│                                                                                │
│   KPIs temps reel · graphe de fraudes · table des transactions               │
│   formulaire de test · explication de la decision (ExplainCard)             │
└───────────────────────────────────────────────────────────────────────────--─┘

3 services orchestres par docker-compose.yml : db (Postgres) → api → dashboard
```

## Résultats du modèle

| Métrique | Valeur | Modèle |
|---|---|---|
| **AUC-ROC** | **0.9836** | Random Forest (retenu) |
| F1-Score | 0.5753 | Random Forest |
| Precision | 0.4279 | Random Forest |
| Recall | 0.8776 | Random Forest |
| Temps de réponse `/predict` | ~25-50ms | mesuré en local |

XGBoost optimisé par GridSearchCV (`n_estimators`, `max_depth`, `learning_rate`) atteint 0.9798 d'AUC-ROC — le Random Forest reste le meilleur des deux, mais l'écart est faible. Détail complet (matrices de confusion, hyperparamètres retenus) dans [`models/evaluation_report.txt`](models/evaluation_report.txt) et la courbe ROC dans [`models/roc_curve.png`](models/roc_curve.png), tous deux régénérés à chaque `python -m src.train`.

> Precision à 0.43 : sur ce dataset très déséquilibré (0.17% de fraudes), le modèle privilégie volontairement le rappel (88%) — rater une fraude coûte plus cher qu'enquêter sur un faux positif. C'est un choix métier, pas une limite technique : le seuil de décision (`DEFAULT_THRESHOLD` dans `api/predictor.py`) peut être ajusté pour déplacer ce compromis.

## Démarrage rapide

```bash
git clone <url-du-repo> && cd fraud-detection
python -m venv venv && source venv/Scripts/activate && pip install -r requirements.txt
python -m src.train          # entraine et sauvegarde models/fraud_model.pkl
docker compose up --build    # lance db + api + dashboard
```

Dashboard sur **http://localhost:3000**, API sur **http://localhost:8000**.

Ou directement via les scripts guidés (vérifient les prérequis, entraînent le modèle si besoin) :

```bash
./scripts/setup.sh     # Linux / macOS / Git Bash
./scripts/setup.ps1    # Windows PowerShell
```

## Endpoints API

| Méthode | Route | Description |
|---|---|---|
| GET | `/health` | Vérifie que l'API et le modèle sont chargés |
| POST | `/predict` | Analyse une transaction et la logge en base |
| POST | `/explain` | Predit + renvoie les 5 features qui ont le plus pesé sur la décision |
| GET | `/stats` | Statistiques globales (total, taux de fraude...) |
| GET | `/transactions?limit=50` | Dernières transactions loggées |

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"Amount": 50.0, "Time": 10000.0}'
# {"is_fraud":false,"confidence":0.027,"transaction_id":"1","timestamp":"..."}

curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{"Amount": 15000.0, "Time": 50000.0, "V14": -9.5}'
# {"prediction":{"is_fraud":true,"confidence":0.71},
#  "explanation":[{"feature":"V14","importance":0.199}, ...],
#  "interpretation":"Les features V14 et V10 ont le plus contribue a cette decision..."}
```

Vérifier tous les endpoints d'un coup : `./scripts/test_api.sh`. Simuler un flux continu de transactions : `python scripts/simulate_transactions.py`. Diagnostic complet du système (modèle, API, DB, dashboard) : `python scripts/health_check.py`.

## Ce que j'ai appris

- **Gestion du déséquilibre de classes** : sur un dataset à 0.17% de fraudes, l'accuracy ne veut rien dire. SMOTE (sur le train set uniquement) et l'AUC-ROC comme métrique d'optimisation ont été les deux décisions qui ont le plus changé les résultats.
- **Architecture microservices** : séparer ML (`src/`), API (`api/`), et frontend (`dashboard/`) en couches indépendantes, chacune avec son propre cycle de build/test, communiquant uniquement par HTTP/JSON.
- **Containerisation multi-service** : 3 conteneurs (Postgres, API, dashboard) orchestrés avec des healthchecks et des dépendances explicites (`depends_on: condition: service_healthy`), pas juste un `docker run` isolé.
- **Explicabilité des modèles ML** : exposer `feature_importances_` via une API a ses limites — c'est une importance globale, pas une explication causale de telle transaction précise. Comprendre cette limite (et pourquoi SHAP existe) a été aussi important que d'implémenter l'endpoint.

## Améliorations futures

- **Pipeline SMOTE+CV plus rigoureux** : appliquer actuellement SMOTE avant la validation croisée du GridSearchCV laisse fuiter de l'information entre les folds (des points synthétiques proches peuvent se retrouver dans le train ET le test du même split). Une `imblearn.pipeline.Pipeline` qui ré-applique SMOTE à chaque fold donnerait un score plus honnête.
- **SHAP values** pour une explicabilité locale réelle (contribution par transaction), au lieu de l'importance globale actuelle.
- **Streaming Kafka** pour ingérer un vrai flux de transactions au lieu du polling toutes les 5s du dashboard.
- **Alertes email/SMS** automatiques au-dessus d'un seuil de confiance.
- **Déploiement cloud** (AWS/GCP) avec CI/CD de bout en bout (la CI actuelle teste et valide ; il manque le déploiement).

## Structure du projet

```
fraud-detection/
├── src/                  # pipeline ML (preprocessing, train, config)
├── api/                  # API FastAPI + tests + Dockerfile
├── dashboard/             # dashboard React + Vite + Dockerfile + nginx.conf
├── scripts/              # setup, tests API, simulation, health check
├── .github/workflows/    # CI (tests + validation docker compose)
├── models/               # fraud_model.pkl, scaler.pkl, rapport, courbe ROC
├── data/                 # creditcard.csv (non commité, voir ci-dessous)
└── docker-compose.yml    # orchestration des 3 services
```

## Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Python 3.11+
- Le dataset Kaggle [Credit Card Fraud Detection](https://www.kaggle.com/mlg-ulb/creditcardfraud), à placer dans `data/creditcard.csv` (144 Mo, non fourni dans le repo)
