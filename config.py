"""
Configuration centralisée du projet Crypto Prediction.
4 cryptos : Bitcoin, Ethereum, Solana, XRP
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Binance ──────────────────────────────────────────
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")

# 4 Cryptos à tracker
SYMBOLS = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "SOL": "SOLUSDT",
    "XRP": "XRPUSDT",
}

CRYPTO_INFO = {
    "BTC": {"name": "Bitcoin",  "icon": "₿", "color": "#F7931A"},
    "ETH": {"name": "Ethereum", "icon": "⟠", "color": "#627EEA"},
    "SOL": {"name": "Solana",   "icon": "◎", "color": "#9945FF"},
    "XRP": {"name": "XRP",      "icon": "✕", "color": "#23292F"},
}

# Intervalles disponibles
INTERVALS = {
    "1h": "1h",
    "4h": "4h",
    "1d": "1d",
}

DEFAULT_INTERVAL = "1d"
# OPTIMIZATION: 90 days max for Serverless/Vercel performance
DEFAULT_LOOKBACK = "90 days ago UTC"

# ── Modèles ──────────────────────────────────────────
PREDICTION_DAYS = 7
LSTM_EPOCHS = 50
LSTM_BATCH_SIZE = 32
LSTM_SEQUENCE_LENGTH = 60

# ── API ──────────────────────────────────────────────
API_HOST = "0.0.0.0"
API_PORT = 8000

# ── Auto-refresh ─────────────────────────────────────
AUTO_REFRESH_SECONDS = 600  # 10 minutes

# ── Paths ────────────────────────────────────────────
import pathlib
import tempfile

BASE_DIR = pathlib.Path(__file__).parent
# Use /tmp (tempfile) for Vercel/Serverless read-only filesystem compatibility
TEMP_DIR = pathlib.Path(tempfile.gettempdir())

DATA_DIR = TEMP_DIR / "crypto_cache"
MODEL_DIR = TEMP_DIR / "crypto_models"

DATA_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)
