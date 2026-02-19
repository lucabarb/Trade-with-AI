"""
FastAPI Backend — API REST pour le système de prédiction crypto.
Endpoints pour les prix, indicateurs, prédictions et sentiment.

Lancer avec: uvicorn api.main:app --reload --port 8000
Docs Swagger: http://localhost:8000/docs
"""
import os
import sys
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Path setup
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

import config
from data.binance_client import get_historical_data, get_latest_price
from data.indicators import add_all_indicators, get_indicator_summary
#Sentiment removed

# ── App ──────────────────────────────────────────────
app = FastAPI(
    title="🚀 Crypto Prediction API",
    description="API de prédiction du prix Bitcoin & Ethereum avec indicateurs techniques (Maths Only).",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ───────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    """Vérifie que l'API est en ligne."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }


# ── Prices ───────────────────────────────────────────
@app.get("/api/prices/{symbol}", tags=["Market Data"])
async def get_prices(
    symbol: str,
    interval: str = Query("1d", description="Intervalle: 1h, 4h, 1d"),
    lookback: str = Query("90 days ago UTC", description="Période de lookback"),
):
    """
    Récupère les données historiques OHLCV avec indicateurs techniques.
    
    - **symbol**: BTC ou ETH
    - **interval**: 1h, 4h, ou 1d
    - **lookback**: Période (ex: '90 days ago UTC')
    """
    symbol = symbol.upper()
    if symbol not in config.SYMBOLS:
        raise HTTPException(status_code=400, detail=f"Symbole invalide: {symbol}. Utilisez BTC ou ETH.")
    
    binance_symbol = config.SYMBOLS[symbol]
    df = get_historical_data(binance_symbol, interval, lookback)
    df = add_all_indicators(df)
    
    # Convertir en JSON
    records = []
    for idx, row in df.iterrows():
        record = {
            "timestamp": idx.isoformat(),
            "open": round(row['open'], 2),
            "high": round(row['high'], 2),
            "low": round(row['low'], 2),
            "close": round(row['close'], 2),
            "volume": round(row['volume'], 2),
        }
        # Ajouter les indicateurs
        for col in ['RSI', 'MACD', 'MACD_signal', 'MACD_hist',
                     'BB_upper', 'BB_middle', 'BB_lower',
                     'EMA_20', 'EMA_50', 'EMA_200', 'ATR']:
            if col in row.index and not (isinstance(row[col], float) and str(row[col]) == 'nan'):
                try:
                    record[col.lower()] = round(float(row[col]), 4)
                except (ValueError, TypeError):
                    pass
        records.append(record)
    
    summary = get_indicator_summary(df)
    
    return {
        "symbol": symbol,
        "interval": interval,
        "data_points": len(records),
        "latest_price": records[-1]['close'] if records else None,
        "summary": summary,
        "data": records[-200:],  # Limiter à 200 points pour la perf
    }


@app.get("/api/price/{symbol}/latest", tags=["Market Data"])
async def get_price_latest(symbol: str):
    """Récupère le dernier prix en temps réel."""
    symbol = symbol.upper()
    if symbol not in config.SYMBOLS:
        raise HTTPException(status_code=400, detail=f"Symbole invalide: {symbol}")
    
    return get_latest_price(config.SYMBOLS[symbol])


# ── Predictions ──────────────────────────────────────
@app.get("/api/predict/{symbol}", tags=["Predictions"])
async def get_predictions(
    symbol: str,
    model: str = Query("prophet", description="Modèle: prophet"),
    days: int = Query(7, description="Jours de prédiction (1-30)", ge=1, le=30),
):
    """
    Lance une prédiction de prix pour le symbole spécifié.
    
    - **symbol**: BTC ou ETH
    - **model**: prophet uniquement
    - **days**: Nombre de jours à prédire (1-30)
    """
    symbol = symbol.upper()
    if symbol not in config.SYMBOLS:
        raise HTTPException(status_code=400, detail=f"Symbole invalide: {symbol}")
    
    binance_symbol = config.SYMBOLS[symbol]
    # OPTIMIZATION: Use 90 days instead of default (365) for faster training on Serverless
    df = get_historical_data(binance_symbol, "1d", "90 days ago UTC")
    df = add_all_indicators(df)
    
    try:
        if model == "prophet":
            from models.prophet_model import train_prophet
            result = train_prophet(df, symbol, days)
        else:
            raise HTTPException(status_code=400, detail="Modèle invalide. Utilisez 'prophet'.")
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de prédiction: {str(e)}")






# ── Dashboard Data ───────────────────────────────────
@app.get("/api/dashboard/{symbol}", tags=["Dashboard"])
async def get_dashboard_data(symbol: str):
    """
    Endpoint agrégé pour le dashboard.
    Retourne prix + indicateurs + sentiment en un seul appel.
    """
    symbol = symbol.upper()
    if symbol not in config.SYMBOLS:
        raise HTTPException(status_code=400, detail=f"Symbole invalide: {symbol}")
    
    binance_symbol = config.SYMBOLS[symbol]
    
    # Données de marché + indicateurs
    df = get_historical_data(binance_symbol, "1d", "90 days ago UTC")
    df = add_all_indicators(df)
    
    # Sentiment
    sentiment = None
    
    # Summary
    summary = get_indicator_summary(df)
    
    # Dernières données pour les graphiques
    chart_data = []
    for idx, row in df.tail(90).iterrows():
        record = {
            "timestamp": idx.isoformat(),
            "open": round(row['open'], 2),
            "high": round(row['high'], 2),
            "low": round(row['low'], 2),
            "close": round(row['close'], 2),
            "volume": round(row['volume'], 2),
        }
        for col in ['RSI', 'MACD', 'MACD_signal', 'BB_upper', 'BB_middle', 'BB_lower',
                     'EMA_20', 'EMA_50']:
            if col in row.index:
                try:
                    val = float(row[col])
                    if not (val != val):  # NaN check
                        record[col.lower()] = round(val, 4)
                except (ValueError, TypeError):
                    pass
        chart_data.append(record)
    
    return {
        "symbol": symbol,
        "current_price": summary.get('price', 0),
        "indicators": summary,
        "sentiment": sentiment,
        "chart_data": chart_data,
        "timestamp": datetime.now().isoformat(),
    }


# ── Startup ──────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    print("\n" + "=" * 50)
    print("🚀 Crypto Prediction API")
    print("=" * 50)
    print(f"  📡 Swagger UI: http://localhost:{config.API_PORT}/docs")
    print(f"  📡 ReDoc:      http://localhost:{config.API_PORT}/redoc")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host=config.API_HOST, port=config.API_PORT, reload=True)
