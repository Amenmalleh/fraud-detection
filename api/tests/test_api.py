"""
Tests de l'API avec TestClient de FastAPI (base sur httpx), qui simule des
requetes HTTP sans avoir besoin de lancer un vrai serveur ni un vrai navigateur.

Pourquoi SQLite en memoire plutot que la vraie base PostgreSQL ?
Pour que les tests tournent partout (CI, machine d'un autre dev) sans avoir
besoin d'un serveur Postgres demarre. On garde le meme modele SQLAlchemy
(Transaction), seul le moteur de base de donnees change.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from api.database import Base, get_db
from api.main import app

# check_same_thread=False + StaticPool : SQLite en memoire n'autorise par
# defaut qu'un seul thread a la fois, mais TestClient peut faire ses appels
# depuis un thread different. StaticPool garde une connexion unique partagee
# au lieu d'en ouvrir une nouvelle (vide) a chaque fois.
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# dependency_overrides est le mecanisme officiel de FastAPI pour remplacer une
# dependance (ici get_db) pendant les tests, sans toucher au code de production.
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True


def test_predict_normal_transaction_is_not_fraud():
    # Transaction "moyenne" : petit montant, toutes les features V* a leur
    # valeur par defaut (0.0, cf. schemas.py). Le modele doit la classer comme legitime.
    payload = {"Amount": 50.0, "Time": 10000.0}

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["is_fraud"] is False
    assert 0.0 <= body["confidence"] <= 1.0
    assert body["transaction_id"]


def test_predict_suspicious_transaction_has_high_confidence():
    # Montant tres eleve (10000+) combine a des features V* fortement
    # decalees de la moyenne : profil typique des fraudes dans ce dataset
    # (les fraudes ont des valeurs V* beaucoup plus extremes que la normale).
    payload = {
        "Amount": 15000.0,
        "Time": 50000.0,
        "V1": -8.0, "V2": 7.5, "V3": -9.0, "V4": 6.5,
        "V10": -7.0, "V12": -8.5, "V14": -9.5, "V17": -6.0,
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["confidence"] > 0.5
    assert body["is_fraud"] is True
