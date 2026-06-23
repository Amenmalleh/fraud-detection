# Image de base legere avec Python preinstalle.
FROM python:3.11-slim

WORKDIR /app

# curl est utilise par le healthcheck HTTP defini dans docker-compose.yml
# (verifie que /health repond avant de considerer le conteneur "sain").
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# On copie d'abord requirements.txt seul : Docker met cette etape en cache et
# ne reinstalle les dependances que si ce fichier change, pas a chaque modif de code.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
