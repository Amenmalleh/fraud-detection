"""
Connexion a PostgreSQL via SQLAlchemy.

Pourquoi SQLAlchemy ?
- C'est un ORM (Object-Relational Mapper) : on definit le modele Transaction
  comme une classe Python normale, et SQLAlchemy genere le SQL a notre place
  (CREATE TABLE, INSERT, SELECT...). On evite d'ecrire du SQL brut partout.
- Il fonctionne avec PostgreSQL en production et SQLite en test (cf.
  api/tests/test_api.py), sans changer une ligne du modele.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func

# Charge les variables du fichier .env (DATABASE_URL, etc.) dans l'environnement.
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/frauddb")

engine = create_engine(DATABASE_URL)

# sessionmaker cree une "fabrique" de sessions : chaque requete HTTP recevra
# sa propre session via get_db(), pour eviter que deux requetes concurrentes
# ne se marchent dessus.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Toutes les classes de modeles (ici Transaction) heritent de Base. C'est ce
# qui permet a SQLAlchemy de savoir quelles tables creer dans init_db().
Base = declarative_base()


class Transaction(Base):
    """Une transaction analysee, loggee en base apres chaque appel a /predict."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    time = Column(Float, nullable=False)
    is_fraud = Column(Boolean, nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    features = Column(JSON, nullable=True)  # snapshot complet (Time, V1..V28, Amount) pour audit


def get_db():
    """
    Dependance FastAPI : ouvre une session par requete et la ferme a la fin,
    meme si une exception est levee (grace au try/finally).

    Usage : def route(db: Session = Depends(get_db)): ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Cree les tables manquantes au demarrage (ne fait rien si elles existent deja)."""
    Base.metadata.create_all(bind=engine)
