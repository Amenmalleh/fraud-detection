"""
Application FastAPI principale : expose le modele de detection de fraude
via une API REST consommable par le dashboard React (ou n'importe quel client HTTP).

Pourquoi FastAPI ?
- Validation automatique des entrees/sorties via Pydantic (cf. schemas.py).
- Documentation interactive generee automatiquement sur /docs.
- Asynchrone et rapide, standard actuel pour les APIs Python en production.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.database import Transaction, get_db, init_db
from api.predictor import FraudPredictor
from api.schemas import ExplainOutput, FeatureImportance, PredictionOutput, PredictionSummary, TransactionInput

# Le modele et le scaler sont charges UNE SEULE FOIS, au demarrage du processus,
# et reutilises pour toutes les requetes suivantes (voir predictor.py).
# Si les fichiers .pkl n'existent pas encore (modele pas encore entraine),
# on demarre quand meme l'API mais /predict repondra une erreur explicite
# plutot que de planter tout le serveur.
try:
    predictor = FraudPredictor()
except FileNotFoundError as exc:
    predictor = None
    print(f"ATTENTION : modele introuvable ({exc}). Lance 'python -m src.train' puis redemarre l'API.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cree les tables PostgreSQL si elles n'existent pas encore, au demarrage du serveur.
    init_db()
    yield


app = FastAPI(title="Fraud Detection API", version="1.0.0", lifespan=lifespan)

# CORS : par defaut, un navigateur bloque les requetes faites depuis un domaine/port
# different de celui de l'API (Cross-Origin Resource Sharing). Le dashboard React
# tourne typiquement sur localhost:3000 (Create React App) ou localhost:5173 (Vite),
# donc on autorise explicitement ces origines a appeler l'API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Verifie que l'API tourne et que le modele a bien ete charge."""
    return {"status": "ok", "model_loaded": predictor is not None}


@app.post("/predict", response_model=PredictionOutput)
def predict(transaction: TransactionInput, db: Session = Depends(get_db)):
    """Predit si une transaction est fraduleuse et logge le resultat en base."""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Modele non charge. Entraine-le avec 'python -m src.train'.")

    data = transaction.model_dump()
    is_fraud, confidence = predictor.predict(data)

    record = Transaction(
        amount=data["Amount"],
        time=data["Time"],
        is_fraud=is_fraud,
        confidence=confidence,
        features=data,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return PredictionOutput(
        is_fraud=is_fraud,
        confidence=confidence,
        transaction_id=str(record.id),
        timestamp=record.created_at or datetime.now(timezone.utc),
    )


@app.post("/explain", response_model=ExplainOutput)
def explain(transaction: TransactionInput):
    """
    Predit une transaction et renvoie en plus les features qui ont le plus
    pese dans la decision (importance globale du modele, cf. ExplainOutput).
    Contrairement a /predict, n'est pas loggee en base : ce n'est pas une
    nouvelle transaction, juste une explication de la meme analyse.
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Modele non charge. Entraine-le avec 'python -m src.train'.")

    data = transaction.model_dump()
    is_fraud, confidence = predictor.predict(data)
    top_features = predictor.top_features(top_n=5)

    top_names = " et ".join(f["feature"] for f in top_features[:2])
    interpretation = (
        f"Les features {top_names} ont le plus contribue a cette decision "
        "(importance globale du modele, pas specifique a cette transaction)."
    )

    return ExplainOutput(
        prediction=PredictionSummary(is_fraud=is_fraud, confidence=confidence),
        explanation=[FeatureImportance(**f) for f in top_features],
        interpretation=interpretation,
    )


@app.get("/stats")
def stats(db: Session = Depends(get_db)):
    """Statistiques globales calculees a partir des transactions loggees en base."""
    total = db.query(func.count(Transaction.id)).scalar() or 0
    total_fraud = (
        db.query(func.count(Transaction.id)).filter(Transaction.is_fraud.is_(True)).scalar() or 0
    )
    avg_confidence = db.query(func.avg(Transaction.confidence)).scalar() or 0.0

    return {
        "total_transactions": total,
        "total_fraud": total_fraud,
        "fraud_rate": round(total_fraud / total, 4) if total else 0.0,
        "avg_confidence": round(float(avg_confidence), 4),
    }


@app.get("/transactions")
def list_transactions(limit: int = 50, db: Session = Depends(get_db)):
    """Renvoie les dernieres transactions loggees, les plus recentes en premier."""
    rows = (
        db.query(Transaction)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": row.id,
            "amount": row.amount,
            "time": row.time,
            "is_fraud": row.is_fraud,
            "confidence": row.confidence,
            "created_at": row.created_at,
        }
        for row in rows
    ]
