"""
Script d'entraînement CLI pour les modèles de prédiction.
Usage:
    python scripts/train.py --model prophet --symbol BTC
    python scripts/train.py --model lstm --symbol ETH
    python scripts/train.py --model both --symbol BTC
"""
import argparse
import os
import sys
import time

# Ajouter le répertoire racine au path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

import config
from data.binance_client import get_historical_data
from data.indicators import add_all_indicators


def main():
    parser = argparse.ArgumentParser(description="🔮 Entraîner les modèles de prédiction crypto")
    parser.add_argument("--model", choices=["prophet", "lstm", "both"], default="prophet",
                        help="Modèle à entraîner")
    parser.add_argument("--symbol", choices=["BTC", "ETH", "both"], default="both",
                        help="Symbole crypto")
    parser.add_argument("--interval", default="1d", help="Intervalle des données")
    parser.add_argument("--lookback", default="365 days ago UTC", help="Période de lookback")
    parser.add_argument("--days", type=int, default=7, help="Jours de prédiction")
    
    args = parser.parse_args()
    
    symbols = ["BTC", "ETH"] if args.symbol == "both" else [args.symbol]
    models = ["prophet", "lstm"] if args.model == "both" else [args.model]
    
    print("=" * 70)
    print("🚀 CRYPTO PREDICTION - TRAINING PIPELINE")
    print("=" * 70)
    print(f"  Symboles : {', '.join(symbols)}")
    print(f"  Modèles  : {', '.join(models)}")
    print(f"  Intervalle: {args.interval}")
    print(f"  Lookback  : {args.lookback}")
    print(f"  Prédiction: {args.days} jours")
    print("=" * 70)
    
    results = {}
    
    for symbol in symbols:
        print(f"\n{'─' * 50}")
        print(f"📊 Chargement des données {symbol}...")
        
        binance_symbol = config.SYMBOLS.get(symbol, f"{symbol}USDT")
        df = get_historical_data(binance_symbol, args.interval, args.lookback)
        df = add_all_indicators(df)
        
        print(f"  → {len(df)} points de données avec {len(df.columns)} features")
        
        for model_name in models:
            print(f"\n🔮 Entraînement {model_name.upper()} pour {symbol}...")
            start_time = time.time()
            
            if model_name == "prophet":
                from models.prophet_model import train_prophet
                result = train_prophet(df, symbol, args.days)
            else:
                from models.lstm_model import train_lstm
                result = train_lstm(df, symbol, args.days)
            
            elapsed = time.time() - start_time
            
            results[f"{symbol}_{model_name}"] = result
            
            print(f"\n  ⏱️  Temps d'entraînement: {elapsed:.1f}s")
            print(f"  📈 Direction: {result['direction']} ({result['predicted_change_pct']:+.2f}%)")
            print(f"  📊 Métriques: {result['metrics']}")
            
            if result['predictions']:
                print(f"\n  🔮 Prédictions {symbol} ({model_name.upper()}):")
                for pred in result['predictions']:
                    print(f"    {pred['date']}: ${pred['predicted_price']:>10,.2f}  "
                          f"[${pred['lower_bound']:>10,.2f} — ${pred['upper_bound']:>10,.2f}]")
    
    # Résumé final
    print(f"\n{'=' * 70}")
    print("📊 RÉSUMÉ FINAL")
    print("=" * 70)
    
    for key, result in results.items():
        symbol, model = key.split('_')
        arrow = "🟢 ↗" if result['direction'] == 'UP' else "🔴 ↘"
        print(f"  {arrow} {symbol} ({model.upper()}): {result['predicted_change_pct']:+.2f}% "
              f"| ${result['current_price']:,.2f} → ${result['predictions'][-1]['predicted_price']:,.2f}")
    
    print(f"\n✅ Modèles sauvegardés dans: {config.MODEL_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
