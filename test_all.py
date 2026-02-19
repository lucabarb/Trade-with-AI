"""Test rapide de tous les modules."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("🧪 TEST: Crypto Prediction Modules")
print("=" * 60)

# 1. Test data ingestion
print("\n1️⃣ Test: Data Ingestion (Binance)...")
from data.binance_client import get_historical_data
df = get_historical_data("BTCUSDT", "1d", "90 days ago UTC")
print(f"   ✅ {len(df)} lignes récupérées pour BTCUSDT")
print(f"   Prix actuel: ${df['close'].iloc[-1]:,.2f}")

# 2. Test indicators
print("\n2️⃣ Test: Indicateurs Techniques...")
from data.indicators import add_all_indicators, get_indicator_summary
df = add_all_indicators(df)
summary = get_indicator_summary(df)
print(f"   ✅ RSI: {summary['rsi']}")
print(f"   ✅ MACD: {summary['macd']}")
print(f"   ✅ Signal global: {summary['overall_signal']}")

# 3. Test sentiment
print("\n3️⃣ Test: Sentiment Analysis...")
from sentiment.reddit_sentiment import analyze_sentiment_reddit
sentiment = analyze_sentiment_reddit("BTC")
print(f"   ✅ Score: {sentiment['sentiment_score']}")
print(f"   ✅ Label: {sentiment['sentiment_label']}")
print(f"   ✅ Source: {sentiment['source']}")

# 4. Test Prophet prediction
print("\n4️⃣ Test: Prophet Prediction...")
from models.prophet_model import train_prophet
result = train_prophet(df, "BTC", 7)
print(f"   ✅ Direction: {result['direction']} ({result['predicted_change_pct']:+.2f}%)")
print(f"   ✅ Prédictions: {len(result['predictions'])} jours")

print("\n" + "=" * 60)
print("✅ TOUS LES TESTS OK!")
print("=" * 60)
print("\nPour lancer le dashboard:")
print("  streamlit run dashboard/app.py")
print("\nPour lancer l'API:")
print("  uvicorn api.main:app --reload --port 8000")
