"""
Indicateurs techniques et règles d'analyse mathématique avancées.
Inclut : RSI, MACD, Bollinger, EMA, ATR, Stochastic, Fibonacci,
Pivot Points, Ichimoku Cloud, divergences, et signaux composites.
"""
import pandas as pd
import numpy as np


# ═══════════════════════════════════════════════════════
# INDICATEURS DE BASE
# ═══════════════════════════════════════════════════════

def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """RSI (Relative Strength Index) — Wilder's smoothing."""
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df


def add_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """MACD (Moving Average Convergence Divergence)."""
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    df['MACD'] = ema_fast - ema_slow
    df['MACD_signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
    df['MACD_hist'] = df['MACD'] - df['MACD_signal']
    return df


def add_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
    """Bandes de Bollinger."""
    sma = df['close'].rolling(window=period).mean()
    std = df['close'].rolling(window=period).std()
    df['BB_upper'] = sma + (std * std_dev)
    df['BB_middle'] = sma
    df['BB_lower'] = sma - (std * std_dev)
    df['BB_width'] = (df['BB_upper'] - df['BB_lower']) / df['BB_middle']
    df['BB_percent'] = (df['close'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'])
    return df


def add_ema(df: pd.DataFrame, periods: list = [9, 21, 50, 200]) -> pd.DataFrame:
    """EMA (Exponential Moving Averages) — 9, 21, 50, 200."""
    for period in periods:
        df[f'EMA_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
    return df


def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """ATR (Average True Range) — mesure de volatilité."""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=period).mean()
    df['ATR_pct'] = (df['ATR'] / df['close']) * 100
    return df


def add_volume_analysis(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """Analyse du volume avec ratio et OBV."""
    df['Volume_SMA'] = df['volume'].rolling(window=period).mean()
    df['Volume_ratio'] = df['volume'] / df['Volume_SMA']
    # OBV (On-Balance Volume)
    df['OBV'] = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
    return df


def add_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
    """Oscillateur Stochastique %K et %D."""
    low_min = df['low'].rolling(window=k_period).min()
    high_max = df['high'].rolling(window=k_period).max()
    df['Stoch_K'] = 100 * (df['close'] - low_min) / (high_max - low_min)
    df['Stoch_D'] = df['Stoch_K'].rolling(window=d_period).mean()
    return df


# ═══════════════════════════════════════════════════════
# INDICATEURS AVANCÉS
# ═══════════════════════════════════════════════════════

def add_fibonacci_levels(df: pd.DataFrame, lookback: int = 50) -> pd.DataFrame:
    """
    Niveaux de Fibonacci basés sur le dernier swing high/low.
    Ratios: 0%, 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100%
    """
    recent = df.tail(lookback)
    high = recent['high'].max()
    low = recent['low'].min()
    diff = high - low
    
    df['Fib_0'] = high                          # 0% (résistance)
    df['Fib_236'] = high - diff * 0.236         # 23.6%
    df['Fib_382'] = high - diff * 0.382         # 38.2%
    df['Fib_500'] = high - diff * 0.500         # 50%
    df['Fib_618'] = high - diff * 0.618         # 61.8% (Golden ratio)
    df['Fib_786'] = high - diff * 0.786         # 78.6%
    df['Fib_100'] = low                         # 100% (support)
    
    return df


def add_pivot_points(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot Points classiques (Floor Trader Pivots).
    PP = (High + Low + Close) / 3
    R1 = 2*PP - Low, S1 = 2*PP - High
    R2 = PP + (High - Low), S2 = PP - (High - Low)
    """
    pp = (df['high'].shift(1) + df['low'].shift(1) + df['close'].shift(1)) / 3
    df['Pivot'] = pp
    df['R1'] = 2 * pp - df['low'].shift(1)
    df['S1'] = 2 * pp - df['high'].shift(1)
    df['R2'] = pp + (df['high'].shift(1) - df['low'].shift(1))
    df['S2'] = pp - (df['high'].shift(1) - df['low'].shift(1))
    df['R3'] = df['high'].shift(1) + 2 * (pp - df['low'].shift(1))
    df['S3'] = df['low'].shift(1) - 2 * (df['high'].shift(1) - pp)
    return df


def add_ichimoku(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ichimoku Cloud (Kumo) — système complet d'analyse.
    Tenkan-sen (conversion), Kijun-sen (base), Senkou Span A/B, Chikou Span.
    """
    # Tenkan-sen (ligne de conversion) — 9 périodes
    high_9 = df['high'].rolling(window=9).max()
    low_9 = df['low'].rolling(window=9).min()
    df['Ichimoku_tenkan'] = (high_9 + low_9) / 2
    
    # Kijun-sen (ligne de base) — 26 périodes
    high_26 = df['high'].rolling(window=26).max()
    low_26 = df['low'].rolling(window=26).min()
    df['Ichimoku_kijun'] = (high_26 + low_26) / 2
    
    # Senkou Span A (leading) — moyenne des deux lignes, projetée 26 périodes
    df['Ichimoku_senkou_a'] = ((df['Ichimoku_tenkan'] + df['Ichimoku_kijun']) / 2).shift(26)
    
    # Senkou Span B (leading) — 52 périodes, projetée 26 périodes
    high_52 = df['high'].rolling(window=52).max()
    low_52 = df['low'].rolling(window=52).min()
    df['Ichimoku_senkou_b'] = ((high_52 + low_52) / 2).shift(26)
    
    return df


def add_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    ADX (Average Directional Index) — force de la tendance.
    ADX > 25 = tendance forte, ADX < 20 = range/consolidation.
    """
    plus_dm = df['high'].diff()
    minus_dm = -df['low'].diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    
    atr = pd.concat([
        df['high'] - df['low'],
        np.abs(df['high'] - df['close'].shift()),
        np.abs(df['low'] - df['close'].shift())
    ], axis=1).max(axis=1).rolling(window=period).mean()
    
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
    
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    df['ADX'] = dx.rolling(window=period).mean()
    df['DI_plus'] = plus_di
    df['DI_minus'] = minus_di
    return df


def add_vwap(df: pd.DataFrame) -> pd.DataFrame:
    """VWAP (Volume Weighted Average Price) — rolling."""
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    df['VWAP'] = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
    return df


# ═══════════════════════════════════════════════════════
# RÈGLES DE TRADING MATHÉMATIQUES
# ═══════════════════════════════════════════════════════

def detect_divergences(df: pd.DataFrame) -> pd.DataFrame:
    """
    Détecte les divergences RSI haussières et baissières.
    - Divergence haussière : prix fait un lower low, RSI fait un higher low → signal d'achat
    - Divergence baissière : prix fait un higher high, RSI fait un lower high → signal de vente
    """
    lookback = 5
    df['Divergence'] = 'NONE'
    
    if 'RSI' not in df.columns or len(df) < lookback * 2:
        return df
    
    for i in range(lookback * 2, len(df)):
        # Vérifier divergence haussière
        price_window = df['close'].iloc[i-lookback:i+1]
        rsi_window = df['RSI'].iloc[i-lookback:i+1]
        
        if price_window.iloc[-1] < price_window.iloc[0] and rsi_window.iloc[-1] > rsi_window.iloc[0]:
            df.iloc[i, df.columns.get_loc('Divergence')] = 'BULLISH_DIV'
        elif price_window.iloc[-1] > price_window.iloc[0] and rsi_window.iloc[-1] < rsi_window.iloc[0]:
            df.iloc[i, df.columns.get_loc('Divergence')] = 'BEARISH_DIV'
    
    return df


def compute_trading_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Système de signaux composites basé sur des règles mathématiques rigoureuses.
    Chaque règle génère un score de -2 à +2.
    Score total détermine le signal global.
    """
    df['Score'] = 0.0
    
    # ── Règle 1 : RSI Zones ──
    if 'RSI' in df.columns:
        df.loc[df['RSI'] < 20, 'Score'] += 2      # Très survendu → fort achat
        df.loc[df['RSI'] < 30, 'Score'] += 1       # Survendu → achat
        df.loc[df['RSI'] > 80, 'Score'] -= 2       # Très suracheté → forte vente
        df.loc[df['RSI'] > 70, 'Score'] -= 1       # Suracheté → vente
    
    # ── Règle 2 : MACD Crossover ──
    if 'MACD' in df.columns and 'MACD_signal' in df.columns:
        # Gold cross : MACD passe au-dessus du signal
        macd_cross_up = (df['MACD'] > df['MACD_signal']) & (df['MACD'].shift(1) <= df['MACD_signal'].shift(1))
        # Death cross : MACD passe en-dessous du signal
        macd_cross_down = (df['MACD'] < df['MACD_signal']) & (df['MACD'].shift(1) >= df['MACD_signal'].shift(1))
        df.loc[macd_cross_up, 'Score'] += 2
        df.loc[macd_cross_down, 'Score'] -= 2
        # MACD histogramme croissant/décroissant
        df.loc[df['MACD_hist'] > 0, 'Score'] += 0.5
        df.loc[df['MACD_hist'] < 0, 'Score'] -= 0.5
    
    # ── Règle 3 : EMA Crossovers (Golden/Death Cross) ──
    if 'EMA_9' in df.columns and 'EMA_21' in df.columns:
        golden_cross = (df['EMA_9'] > df['EMA_21']) & (df['EMA_9'].shift(1) <= df['EMA_21'].shift(1))
        death_cross = (df['EMA_9'] < df['EMA_21']) & (df['EMA_9'].shift(1) >= df['EMA_21'].shift(1))
        df.loc[golden_cross, 'Score'] += 2
        df.loc[death_cross, 'Score'] -= 2
    
    if 'EMA_50' in df.columns and 'EMA_200' in df.columns:
        # EMA 50/200 — trend direction
        df.loc[df['EMA_50'] > df['EMA_200'], 'Score'] += 1
        df.loc[df['EMA_50'] < df['EMA_200'], 'Score'] -= 1
    
    # ── Règle 4 : Bollinger Bands Squeeze & Bounce ──
    if 'BB_percent' in df.columns:
        df.loc[df['BB_percent'] < 0, 'Score'] += 1.5     # Sous la bande basse → achat
        df.loc[df['BB_percent'] > 1, 'Score'] -= 1.5     # Au-dessus de la bande haute → vente
        # Squeeze (faible volatilité → breakout imminent)
        if 'BB_width' in df.columns:
            bb_width_mean = df['BB_width'].rolling(20).mean()
            df.loc[df['BB_width'] < bb_width_mean * 0.5, 'Score'] += 0.5  # Squeeze détecté
    
    # ── Règle 5 : Stochastic ──
    if 'Stoch_K' in df.columns and 'Stoch_D' in df.columns:
        stoch_cross_up = (df['Stoch_K'] > df['Stoch_D']) & (df['Stoch_K'].shift(1) <= df['Stoch_D'].shift(1)) & (df['Stoch_K'] < 20)
        stoch_cross_down = (df['Stoch_K'] < df['Stoch_D']) & (df['Stoch_K'].shift(1) >= df['Stoch_D'].shift(1)) & (df['Stoch_K'] > 80)
        df.loc[stoch_cross_up, 'Score'] += 2
        df.loc[stoch_cross_down, 'Score'] -= 2
    
    # ── Règle 6 : ADX Trend Strength ──
    if 'ADX' in df.columns:
        # ADX > 25 confirme la tendance
        strong_trend = df['ADX'] > 25
        if 'DI_plus' in df.columns and 'DI_minus' in df.columns:
            df.loc[strong_trend & (df['DI_plus'] > df['DI_minus']), 'Score'] += 1
            df.loc[strong_trend & (df['DI_plus'] < df['DI_minus']), 'Score'] -= 1
    
    # ── Règle 7 : Volume Confirmation ──
    if 'Volume_ratio' in df.columns:
        high_vol = df['Volume_ratio'] > 1.5
        price_up = df['close'] > df['close'].shift(1)
        price_down = df['close'] < df['close'].shift(1)
        df.loc[high_vol & price_up, 'Score'] += 1  # Volume confirme hausse
        df.loc[high_vol & price_down, 'Score'] -= 1  # Volume confirme baisse
    
    # ── Règle 8 : Divergences RSI ──
    if 'Divergence' in df.columns:
        df.loc[df['Divergence'] == 'BULLISH_DIV', 'Score'] += 2
        df.loc[df['Divergence'] == 'BEARISH_DIV', 'Score'] -= 2
    
    # ── Règle 9 : Fibonacci Support/Resistance ──
    if 'Fib_618' in df.columns:
        near_fib_618 = np.abs(df['close'] - df['Fib_618']) / df['close'] < 0.01
        near_fib_382 = np.abs(df['close'] - df['Fib_382']) / df['close'] < 0.01
        df.loc[near_fib_618, 'Score'] += 1  # Rebond potentiel au golden ratio
        df.loc[near_fib_382, 'Score'] += 0.5
    
    # ── Règle 10 : Pivot Points ──
    if 'Pivot' in df.columns:
        df.loc[df['close'] > df['R1'], 'Score'] += 0.5   # Au-dessus de R1 = bullish
        df.loc[df['close'] > df['R2'], 'Score'] += 0.5   # Au-dessus de R2 = très bullish
        df.loc[df['close'] < df['S1'], 'Score'] -= 0.5   # Sous S1 = bearish
        df.loc[df['close'] < df['S2'], 'Score'] -= 0.5   # Sous S2 = très bearish
    
    # ── Signal global ──
    df['Signal_strength'] = df['Score'].rolling(3).mean()  # Lissage sur 3 périodes
    
    df['Signal'] = 'NEUTRAL'
    df.loc[df['Signal_strength'] > 3, 'Signal'] = 'STRONG_BUY'
    df.loc[(df['Signal_strength'] > 1) & (df['Signal_strength'] <= 3), 'Signal'] = 'BUY'
    df.loc[df['Signal_strength'] < -3, 'Signal'] = 'STRONG_SELL'
    df.loc[(df['Signal_strength'] < -1) & (df['Signal_strength'] >= -3), 'Signal'] = 'SELL'
    
    return df


# ═══════════════════════════════════════════════════════
# PIPELINE COMPLET
# ═══════════════════════════════════════════════════════

def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute TOUS les indicateurs et signaux au DataFrame."""
    df = df.copy()
    df = add_rsi(df)
    df = add_macd(df)
    df = add_bollinger_bands(df)
    df = add_ema(df)
    df = add_atr(df)
    df = add_volume_analysis(df)
    df = add_stochastic(df)
    df = add_fibonacci_levels(df)
    df = add_pivot_points(df)
    df = add_ichimoku(df)
    df = add_adx(df)
    df = add_vwap(df)
    df = detect_divergences(df)
    df = compute_trading_signals(df)
    return df


def get_indicator_summary(df: pd.DataFrame) -> dict:
    """Résumé complet des indicateurs et du signal de trading."""
    if df.empty:
        return {}
    
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    # Variation 24h
    change_pct = ((latest['close'] - prev['close']) / prev['close']) * 100
    
    # Résumé des signaux actifs
    active_rules = []
    
    rsi = latest.get('RSI', 50)
    if rsi < 30:
        active_rules.append(("RSI Survendu", "BUY", f"RSI = {rsi:.1f} < 30"))
    elif rsi > 70:
        active_rules.append(("RSI Suracheté", "SELL", f"RSI = {rsi:.1f} > 70"))
    
    if latest.get('MACD', 0) > latest.get('MACD_signal', 0):
        active_rules.append(("MACD Bullish", "BUY", "MACD > Signal"))
    else:
        active_rules.append(("MACD Bearish", "SELL", "MACD < Signal"))
    
    if latest.get('EMA_50', 0) > latest.get('EMA_200', 0):
        active_rules.append(("Golden Cross (50/200)", "BUY", "EMA50 > EMA200"))
    elif latest.get('EMA_50', 0) < latest.get('EMA_200', 0):
        active_rules.append(("Death Cross (50/200)", "SELL", "EMA50 < EMA200"))
    
    adx = latest.get('ADX', 0)
    if adx > 25:
        trend_dir = "haussière" if latest.get('DI_plus', 0) > latest.get('DI_minus', 0) else "baissière"
        active_rules.append(("Tendance Forte (ADX)", "BUY" if trend_dir == "haussière" else "SELL", f"ADX = {adx:.1f}, tendance {trend_dir}"))
    else:
        active_rules.append(("Range / Consolidation", "NEUTRAL", f"ADX = {adx:.1f} < 25"))
    
    bb_pct = latest.get('BB_percent', 0.5)
    if bb_pct < 0:
        active_rules.append(("Bollinger Oversold", "BUY", "Prix sous bande basse"))
    elif bb_pct > 1:
        active_rules.append(("Bollinger Overbought", "SELL", "Prix au-dessus bande haute"))
    
    stoch_k = latest.get('Stoch_K', 50)
    if stoch_k < 20:
        active_rules.append(("Stochastic Survendu", "BUY", f"%K = {stoch_k:.1f}"))
    elif stoch_k > 80:
        active_rules.append(("Stochastic Suracheté", "SELL", f"%K = {stoch_k:.1f}"))
    
    div = latest.get('Divergence', 'NONE')
    if div == 'BULLISH_DIV':
        active_rules.append(("Divergence Haussière RSI", "BUY", "Prix ↘ + RSI ↗"))
    elif div == 'BEARISH_DIV':
        active_rules.append(("Divergence Baissière RSI", "SELL", "Prix ↗ + RSI ↘"))
    
    # Score et signal
    score = latest.get('Signal_strength', 0)
    signal = latest.get('Signal', 'NEUTRAL')
    
    summary = {
        "price": round(float(latest['close']), 2),
        "change_pct": round(float(change_pct), 2),
        "rsi": round(float(rsi), 2),
        "macd": round(float(latest.get('MACD', 0)), 4),
        "macd_signal": round(float(latest.get('MACD_signal', 0)), 4),
        "macd_hist": round(float(latest.get('MACD_hist', 0)), 4),
        "bb_upper": round(float(latest.get('BB_upper', 0)), 2),
        "bb_lower": round(float(latest.get('BB_lower', 0)), 2),
        "bb_width": round(float(latest.get('BB_width', 0)), 4),
        "bb_percent": round(float(bb_pct), 4),
        "atr": round(float(latest.get('ATR', 0)), 2),
        "atr_pct": round(float(latest.get('ATR_pct', 0)), 2),
        "adx": round(float(adx), 2),
        "stoch_k": round(float(stoch_k), 2),
        "ema_9": round(float(latest.get('EMA_9', 0)), 2),
        "ema_21": round(float(latest.get('EMA_21', 0)), 2),
        "ema_50": round(float(latest.get('EMA_50', 0)), 2),
        "ema_200": round(float(latest.get('EMA_200', 0)), 2),
        "volume_ratio": round(float(latest.get('Volume_ratio', 0)), 2),
        "pivot": round(float(latest.get('Pivot', 0)), 2),
        "r1": round(float(latest.get('R1', 0)), 2),
        "s1": round(float(latest.get('S1', 0)), 2),
        "fib_618": round(float(latest.get('Fib_618', 0)), 2),
        "fib_382": round(float(latest.get('Fib_382', 0)), 2),
        "score": round(float(score), 2),
        "signal": signal,
        "active_rules": active_rules,
    }
    
    return summary
