"""
Module de récupération des données — API publique Binance.
Pas de clé API nécessaire pour les données OHLCV historiques.
Pas de cache fichier : Streamlit gère le cache en mémoire.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def get_historical_data(symbol: str = "BTCUSDT", interval: str = "1d", lookback: str = "365 days ago UTC") -> pd.DataFrame:
    """
    Récupère les données historiques OHLCV depuis l'API publique Binance.
    Toujours en temps réel — pas de cache fichier.
    """
    try:
        from binance.client import Client
        client = Client("", "")  # Pas de clé = API publique
        
        klines = client.get_historical_klines(symbol, interval, lookback)
        
        if not klines:
            raise ValueError(f"Aucune donnée retournée pour {symbol}")
        
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        df.set_index('timestamp', inplace=True)
        
        # La dernière bougie peut être incomplète (en cours)
        # On la garde pour avoir le prix le plus récent
        
        latest_date = df.index[-1].strftime('%Y-%m-%d %H:%M')
        print(f"✅ {len(df)} bougies {symbol} ({interval}) — dernière: {latest_date}")
        return df
        
    except Exception as e:
        print(f"❌ Erreur Binance {symbol}: {e}")
        raise ValueError(f"Impossible de récupérer les données pour {symbol}: {e}")


def get_latest_price(symbol: str = "BTCUSDT") -> dict:
    """Récupère le dernier prix en temps réel."""
    try:
        from binance.client import Client
        client = Client("", "")
        ticker = client.get_symbol_ticker(symbol=symbol)
        return {
            "symbol": symbol,
            "price": float(ticker['price']),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"symbol": symbol, "price": 0, "error": str(e)}


if __name__ == "__main__":
    for sym in config.SYMBOLS.values():
        df = get_historical_data(sym, "1d", "7 days ago UTC")
        print(f"  Dernière bougie: {df.index[-1]} = ${df['close'].iloc[-1]:,.2f}")
        print(f"  Dates: {df.index[0].strftime('%Y-%m-%d')} → {df.index[-1].strftime('%Y-%m-%d')}")
        print()
