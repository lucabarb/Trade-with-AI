# 🚀 Trade With AI — Crypto Prediction (Maths Only)

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Prophet](https://img.shields.io/badge/Prophet-Meta-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green?logo=fastapi)
![HTML5](https://img.shields.io/badge/Frontend-HTML%2FJS-orange)

> Système de prédiction du prix **Bitcoin** et **Ethereum** basé sur **10 règles mathématiques** et le modèle statistique **Prophet**.
> Projet optimisé, léger et fluide : pas de sentiment, pas de deep learning lourd.

## 🎯 Features

- **📊 Données en temps réel** — API Binance publique (gratuit)
- **📈 Indicateurs techniques** — RSI, MACD, Bollinger Bands, EMA, ATR, Stochastic, Pivot Points, Fibonacci
- **🔮 Prédictions Statistiques** — Facebook Prophet (Projection 7 jours)
- **🚀 API REST** — FastAPI avec Swagger UI
- **💻 Frontend Web** — Interface HTML/JS fluide avec Dark Mode et TradingView charts
- **🐳 Docker ready** — Déploiement facile

## 🏗️ Architecture

```
Trade-with-AI/
├── config.py                 # Configuration
├── data/
│   ├── binance_client.py     # API Binance
│   └── indicators.py         # Cœur mathématique (10 règles)
├── models/
│   └── prophet_model.py      # Modèle prédiction Prophet
├── api/
│   └── main.py               # Backend FastAPI
├── web/                      # Frontend (HTML/JS/CSS)
│   ├── index.html
│   ├── app.js
│   └── style.css
└── requirements.txt
```

## 🚀 Installation

```bash
# 1. Cloner le repo
git clone https://github.com/lucabarb/Trade-with-AI.git
cd Trade-with-AI

# 2. Créer un environnement virtuel
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Installer les dépendances (Léger : ~1 min)
pip install -r requirements.txt
```

## 💻 Utilisation

Lancer les deux serveurs (dans deux terminaux séparés) :

### 1. Backend (Calculs & Prédictions)
```bash
uvicorn api.main:app --reload --port 8000
```
→ API Swagger : http://localhost:8000/docs

### 2. Frontend (Interface Utilisateur)
```bash
python -m http.server 8081 --directory web
```
→ **Ouvrir http://localhost:8081**

## 🛠️ Stack Technique

| Composant | Technologie | Coût |
|-----------|-------------|------|
| Données marché | Binance API publique | ✅ Gratuit |
| Indicateurs | ta (Technical Analysis) | ✅ Gratuit |
| Prédiction | Facebook Prophet | ✅ Gratuit |
| Backend | FastAPI | ✅ Gratuit |
| Frontend | HTML5 / CSS3 / Vanilla JS | ✅ Gratuit |

## ⚠️ Disclaimer

> Ce projet est à but **éducatif uniquement**. Les prédictions sont basées sur des statistiques passées et des indicateurs mathématiques.
> Le marché des cryptomonnaies est volatil.

## 📄 Licence

MIT License
