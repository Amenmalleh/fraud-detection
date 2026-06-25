# Ce Dockerfile vit dans api/ pour l'organisation, mais il est construit
# avec un contexte = racine du projet (voir docker-compose.yml a la racine :
# "context: .", "dockerfile: api/Dockerfile"). Raison : l'API importe le
# package src/ (api/predictor.py fait "from src.config import ..."), donc
# l'image a besoin a la fois de src/ et de api/.

# ---- Stage 1 : builder ----
# On installe les dependances Python dans un prefix isole (/install) avec ce
# stage "jetable". Le stage final ne recuperera que ce dossier, jamais le
# cache pip ni les eventuels outils de compilation utilises ici : l'image
# finale reste petite.
FROM python:3.11-slim AS builder

WORKDIR /build

# api/requirements.txt (pas le requirements.txt racine) : l'API n'a pas besoin
# de jupyter/matplotlib/seaborn/imbalanced-learn, qui ne servent qu'a
# l'entrainement (src/). Les garder hors de l'image runtime evite des dizaines
# de packages inutiles (jupyter seul en entraine une trentaine).
COPY api/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Stage 2 : runtime ----
FROM python:3.11-slim

WORKDIR /app

# curl est utilise par le healthcheck HTTP defini dans docker-compose.yml
# (GET /health toutes les 10s).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Recupere uniquement les packages Python deja installes au stage builder.
COPY --from=builder /install /usr/local

COPY src/ ./src/
COPY api/ ./api/
COPY models/ ./models/

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
