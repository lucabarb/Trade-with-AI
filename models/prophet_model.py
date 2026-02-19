"""
Modèle de prédiction Prophet (Facebook/Meta).
Utilise une transformation log pour garantir des prix positifs
et éviter les extrapolations aberrantes.
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import joblib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def train_prophet(df: pd.DataFrame, symbol: str = "BTC", prediction_days: int = None) -> dict:
    """
    Entraîne un modèle Prophet sur les données historiques.
    
    Utilise log(close) pour:
    - Garantir que les prédictions sont toujours positives
    - Mieux modéliser les variations proportionnelles (%)
    - Éviter les tendances linéaires aberrantes sur des prix élevés
    
    PAS de regressors externes (RSI, MACD) car ils causent
    des extrapolations folles quand on les fixe à une constante.
    """
    from prophet import Prophet
    
    if prediction_days is None:
        prediction_days = config.PREDICTION_DAYS
    
    # Préparer les données — transformation LOG
    prophet_df = pd.DataFrame({
        'ds': df.index,
        'y': np.log(df['close'].values),  # LOG transform
    })
    
    prophet_df = prophet_df.dropna().reset_index(drop=True)
    
    if len(prophet_df) < 15:
        raise ValueError(f"Pas assez de données ({len(prophet_df)} lignes)")
    
    # Supprimer les logs Prophet
    import logging
    logging.getLogger('prophet').setLevel(logging.WARNING)
    logging.getLogger('cmdstanpy').setLevel(logging.WARNING)
    
    # Modèle Prophet — paramètres adaptés aux cryptos & optimisés pour Serverless (Vercel)
    model = Prophet(
        daily_seasonality=False,       # Pas de saisonnalité journalière sur du daily
        weekly_seasonality=True,       # Effet jour de la semaine
        yearly_seasonality=True,       # Cycles annuels
        changepoint_prior_scale=0.1,   # Flexibilité modérée
        seasonality_prior_scale=5,     # Régularisation saisonnalité
        changepoint_range=0.9,         # Changepoints sur 90% des données
        growth='linear',
        uncertainty_samples=0,         # CRITICAL: 0 pour éviter timeout sur Vercel (1000 par défaut = trop lent)
    )
    
    model.fit(prophet_df)
    
    # Prédictions futures
    future = model.make_future_dataframe(periods=prediction_days)
    forecast = model.predict(future)
    
    # Extraire prédictions futures
    last_known_date = prophet_df['ds'].max()
    future_preds = forecast[forecast['ds'] > last_known_date].copy()
    
    # Inverse LOG → prix réels
    predictions = []
    for _, row in future_preds.iterrows():
        pred_price = np.exp(row['yhat'])
        
        # Avec uncertainty_samples=0, yhat_lower/upper n'existent pas ou sont égaux à yhat
        # On simule une marge d'erreur de 5% pour l'affichage
        lower = np.exp(row.get('yhat_lower', row['yhat']))
        upper = np.exp(row.get('yhat_upper', row['yhat']))
        
        if lower == pred_price:
            lower = pred_price * 0.95
            upper = pred_price * 1.05
            
        predictions.append({
            "date": row['ds'].strftime("%Y-%m-%d"),
            "predicted_price": round(float(pred_price), 2),
            "lower_bound": round(float(lower), 2),
            "upper_bound": round(float(upper), 2),
        })
    
    # Métriques in-sample (derniers 20%)
    eval_size = max(1, int(len(prophet_df) * 0.2))
    eval_data = prophet_df.iloc[-eval_size:]
    eval_forecast = forecast[forecast['ds'].isin(eval_data['ds'])]
    
    if len(eval_forecast) > 0:
        # Comparer en prix réels (pas en log)
        actual = np.exp(eval_data['y'].values[:len(eval_forecast)])
        predicted = np.exp(eval_forecast['yhat'].values[:len(actual)])
        
        mae = float(np.mean(np.abs(actual - predicted)))
        rmse = float(np.sqrt(np.mean((actual - predicted) ** 2)))
        mape = float(np.mean(np.abs((actual - predicted) / actual)) * 100)
    else:
        mae = rmse = mape = 0
    
    # Sauvegarder
    model_path = config.MODEL_DIR / f"prophet_{symbol}.pkl"
    joblib.dump(model, model_path)
    
    # Résultats
    current_price = float(df['close'].iloc[-1])
    predicted_end = predictions[-1]['predicted_price'] if predictions else current_price
    change_pct = ((predicted_end - current_price) / current_price) * 100
    
    # Limiter le % de changement à un range réaliste (max ±50% sur la période)
    max_change = min(50, prediction_days * 5)  # ~5% par jour max
    change_pct = max(-max_change, min(max_change, change_pct))
    
    result = {
        "model": "Prophet",
        "symbol": symbol,
        "current_price": round(current_price, 2),
        "predictions": predictions,
        "predicted_change_pct": round(change_pct, 2),
        "direction": "UP" if change_pct > 0 else "DOWN",
        "metrics": {
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "mape": round(mape, 2),
        },
        "trained_on": len(prophet_df),
        "prediction_days": prediction_days,
        "timestamp": datetime.now().isoformat(),
    }
    
    print(f"✅ Prophet {symbol}: {result['direction']} {abs(change_pct):.2f}%")
    print(f"   ${current_price:,.2f} → ${predicted_end:,.2f}")
    print(f"   RMSE: ${rmse:.2f} | MAE: ${mae:.2f} | MAPE: {mape:.2f}%")
    
    return result


def load_and_predict(symbol: str = "BTC", df: pd.DataFrame = None) -> dict:
    """Charge les données et lance une prédiction."""
    if df is None:
        from data.binance_client import get_historical_data
        from data.indicators import add_all_indicators
        binance_symbol = config.SYMBOLS.get(symbol, f"{symbol}USDT")
        df = get_historical_data(binance_symbol, "1d", config.DEFAULT_LOOKBACK)
        df = add_all_indicators(df)
    
    return train_prophet(df, symbol)


if __name__ == "__main__":
    from data.binance_client import get_historical_data
    from data.indicators import add_all_indicators
    
    for sym, bsym in config.SYMBOLS.items():
        print(f"\n{'='*60}")
        print(f"🔮 Prophet — {sym}")
        print('='*60)
        
        df = get_historical_data(bsym, "1d", "365 days ago UTC")
        df = add_all_indicators(df)
        
        result = train_prophet(df, sym, prediction_days=21)
        
        print(f"\nPrédictions {sym}:")
        for pred in result['predictions'][:5]:
            print(f"  {pred['date']}: ${pred['predicted_price']:,.2f} "
                  f"[${pred['lower_bound']:,.2f} - ${pred['upper_bound']:,.2f}]")
        print(f"  ... (+{len(result['predictions'])-5} jours)")
