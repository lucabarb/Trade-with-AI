# Multi-stage Dockerfile pour Crypto Prediction
# FastAPI (port 8000) + Streamlit (port 8501)

FROM python:3.11-slim

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p data/cache models/saved

# Exposer les ports
EXPOSE 8000 8501

# Script de démarrage
COPY <<'EOF' /start.sh
#!/bin/bash
# Lancer FastAPI en arrière-plan
uvicorn api.main:app --host 0.0.0.0 --port 8000 &
# Lancer Streamlit
streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
EOF

RUN chmod +x /start.sh

CMD ["/start.sh"]
