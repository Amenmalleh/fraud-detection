# Contexte de build = dashboard/ (ce dossier est autonome, contrairement a
# l'API : pas besoin de fichiers en dehors de dashboard/ pour le construire).

# ---- Stage 1 : builder ----
# "npm ci" (pas "npm install") : installe exactement les versions figees dans
# package-lock.json, de facon reproductible. C'est la commande recommandee
# pour les builds CI/Docker, "npm install" est reserve au developpement local.
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---- Stage 2 : runtime ----
# nginx:alpine : un serveur web statique tres leger, suffisant pour servir
# le build React (que des fichiers HTML/CSS/JS, plus besoin de Node.js
# une fois le build termine).
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
