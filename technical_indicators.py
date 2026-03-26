"""
Technical Indicators Module
Calculates a full suite of technical indicators on OHLCV data.
"""
import pandas as pd
import numpy as np
import ta

import config


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all technical indicators on OHLCV DataFrame.
    
    Args:
        df: DataFrame with columns Open, High, Low, Close, Volume
    
    Returns:
        DataFrame with original + indicator columns
    """
    if df.empty or len(df) < 14:
        return df

    data = df.copy()

    # Ensure column names are clean
    col_map = {}
    for col in data.columns:
        cl = col.lower().strip()
        if "open" in cl:
            col_map[col] = "Open"
        elif "high" in cl:
            col_map[col] = "High"
        elif "low" in cl:
            col_map[col] = "Low"
        elif "close" in cl:
            col_map[col] = "Close"
        elif "volume" in cl:
            col_map[col] = "Volume"
    data = data.rename(columns=col_map)

    close = data["Close"]
    high = data["High"]
    low = data["Low"]
    volume = data["Volume"].astype(float)

    # ----------------------------------------------------------
    # TREND INDICATORS
    # ----------------------------------------------------------
    # Simple Moving Averages
    for period in config.SMA_PERIODS:
        data[f"SMA_{period}"] = ta.trend.sma_indicator(close, window=period)

    # Exponential Moving Averages
    for period in config.EMA_PERIODS:
        data[f"EMA_{period}"] = ta.trend.ema_indicator(close, window=period)

    # MACD
    macd = ta.trend.MACD(close, window_slow=config.MACD_SLOW,
                          window_fast=config.MACD_FAST, window_sign=config.MACD_SIGNAL)
    data["MACD"] = macd.macd()
    data["MACD_Signal"] = macd.macd_signal()
    data["MACD_Hist"] = macd.macd_diff()

    # ADX
    adx = ta.trend.ADXIndicator(high, low, close, window=config.ADX_PERIOD)
    data["ADX"] = adx.adx()
    data["ADX_Pos"] = adx.adx_pos()
    data["ADX_Neg"] = adx.adx_neg()

    # ----------------------------------------------------------
    # MOMENTUM INDICATORS
    # ----------------------------------------------------------
    # RSI
    data["RSI"] = ta.momentum.rsi(close, window=config.RSI_PERIOD)

    # Stochastic Oscillator
    stoch = ta.momentum.StochasticOscillator(high, low, close, window=config.STOCH_PERIOD)
    data["Stoch_K"] = stoch.stoch()
    data["Stoch_D"] = stoch.stoch_signal()

    # Williams %R
    data["Williams_R"] = ta.momentum.williams_r(high, low, close, lbp=config.WILLIAMS_PERIOD)

    # CCI
    data["CCI"] = ta.trend.cci(high, low, close, window=config.CCI_PERIOD)

    # Rate of Change
    data["ROC"] = ta.momentum.roc(close, window=12)

    # ----------------------------------------------------------
    # VOLATILITY INDICATORS
    # ----------------------------------------------------------
    # Bollinger Bands
    bb = ta.volatility.BollingerBands(close, window=config.BB_PERIOD, window_dev=config.BB_STD)
    data["BB_Upper"] = bb.bollinger_hband()
    data["BB_Middle"] = bb.bollinger_mavg()
    data["BB_Lower"] = bb.bollinger_lband()
    data["BB_Width"] = bb.bollinger_wband()
    data["BB_PctB"] = bb.bollinger_pband()

    # ATR
    data["ATR"] = ta.volatility.average_true_range(high, low, close, window=config.ATR_PERIOD)

    # ----------------------------------------------------------
    # VOLUME INDICATORS
    # ----------------------------------------------------------
    # On Balance Volume
    data["OBV"] = ta.volume.on_balance_volume(close, volume)

    # Volume SMA ratio
    vol_sma = volume.rolling(window=20).mean()
    data["Volume_Ratio"] = volume / vol_sma.replace(0, np.nan)

    # VWAP (approximation)
    typical_price = (high + low + close) / 3
    data["VWAP"] = (typical_price * volume).cumsum() / volume.cumsum()

    # ----------------------------------------------------------
    # DERIVED FEATURES
    # ----------------------------------------------------------
    # Price position relative to MAs
    if "SMA_20" in data.columns:
        data["Price_vs_SMA20"] = (close - data["SMA_20"]) / data["SMA_20"] * 100
    if "SMA_50" in data.columns:
        data["Price_vs_SMA50"] = (close - data["SMA_50"]) / data["SMA_50"] * 100
    if "SMA_200" in data.columns:
        data["Price_vs_SMA200"] = (close - data["SMA_200"]) / data["SMA_200"] * 100

    # Golden/Death cross signals
    if "SMA_50" in data.columns and "SMA_200" in data.columns:
        data["Golden_Cross"] = ((data["SMA_50"] > data["SMA_200"]) &
                                 (data["SMA_50"].shift(1) <= data["SMA_200"].shift(1))).astype(int)
        data["Death_Cross"] = ((data["SMA_50"] < data["SMA_200"]) &
                                (data["SMA_50"].shift(1) >= data["SMA_200"].shift(1))).astype(int)

    # Price momentum (returns)
    data["Return_1d"] = close.pct_change(1)
    data["Return_5d"] = close.pct_change(5)
    data["Return_10d"] = close.pct_change(10)
    data["Return_20d"] = close.pct_change(20)

    # Volatility
    data["Volatility_20d"] = data["Return_1d"].rolling(window=20).std() * np.sqrt(252)

    # Support and Resistance (rolling high/low)
    data["Resistance_20"] = high.rolling(window=20).max()
    data["Support_20"] = low.rolling(window=20).min()
    data["Price_Position"] = (close - data["Support_20"]) / (
        data["Resistance_20"] - data["Support_20"]
    ).replace(0, np.nan)

    return data


def generate_technical_score(df: pd.DataFrame) -> float:
    """
    Generate a 0-100 technical score based on the last row of indicators.
    Higher = more bullish.
    """
    if df.empty or len(df) < 2:
        return 50.0

    last = df.iloc[-1]
    score = 50.0  # Neutral base
    points = 0
    max_points = 0

    # --- RSI ---
    if "RSI" in last and not pd.isna(last["RSI"]):
        max_points += 10
        rsi = last["RSI"]
        if rsi < 30:
            points += 10  # Oversold = bullish
        elif rsi < 40:
            points += 7
        elif rsi < 60:
            points += 5  # Neutral
        elif rsi < 70:
            points += 3
        else:
            points += 0  # Overbought = bearish

    # --- MACD ---
    if "MACD_Hist" in last and not pd.isna(last["MACD_Hist"]):
        max_points += 10
        if last["MACD_Hist"] > 0:
            points += 8
            if "MACD_Hist" in df.columns and len(df) > 1 and df["MACD_Hist"].iloc[-2] < 0:
                points += 2  # Bullish crossover
        else:
            points += 2

    # --- Moving Average Trend ---
    if "Price_vs_SMA20" in last and not pd.isna(last["Price_vs_SMA20"]):
        max_points += 10
        if last["Price_vs_SMA20"] > 0:
            points += 7
        else:
            points += 3

    if "Price_vs_SMA50" in last and not pd.isna(last["Price_vs_SMA50"]):
        max_points += 10
        if last["Price_vs_SMA50"] > 0:
            points += 7
        else:
            points += 3

    # --- ADX (Trend Strength) ---
    if "ADX" in last and not pd.isna(last["ADX"]):
        max_points += 10
        adx = last["ADX"]
        if adx > 25:
            # Strong trend - check direction
            if last.get("ADX_Pos", 0) > last.get("ADX_Neg", 0):
                points += 10  # Strong uptrend
            else:
                points += 2   # Strong downtrend
        else:
            points += 5  # Weak trend

    # --- Bollinger Bands ---
    if "BB_PctB" in last and not pd.isna(last["BB_PctB"]):
        max_points += 10
        pctb = last["BB_PctB"]
        if pctb < 0.2:
            points += 8  # Near lower band = bullish
        elif pctb < 0.5:
            points += 6
        elif pctb < 0.8:
            points += 4
        else:
            points += 2  # Near upper band

    # --- Volume ---
    if "Volume_Ratio" in last and not pd.isna(last["Volume_Ratio"]):
        max_points += 10
        if last["Volume_Ratio"] > 1.5 and last.get("Return_1d", 0) > 0:
            points += 10  # High volume up move
        elif last["Volume_Ratio"] > 1.0:
            points += 6
        else:
            points += 4

    # --- Stochastic ---
    if "Stoch_K" in last and not pd.isna(last["Stoch_K"]):
        max_points += 10
        k = last["Stoch_K"]
        if k < 20:
            points += 9   # Oversold
        elif k < 50:
            points += 6
        elif k < 80:
            points += 4
        else:
            points += 1   # Overbought

    # Normalize to 0-100
    if max_points > 0:
        score = (points / max_points) * 100
    
    return round(score, 2)


def generate_fundamental_score(fundamentals: dict) -> float:
    """
    Generate a 0-100 fundamental score.
    Higher = stronger fundamentals.
    """
    if not fundamentals:
        return 50.0

    score = 0
    max_points = 0

    # P/E Ratio (lower is better, but not negative)
    pe = fundamentals.get("PE")
    if pe is not None and pe > 0:
        max_points += 15
        if pe < 15:
            score += 15
        elif pe < 25:
            score += 10
        elif pe < 40:
            score += 5
        else:
            score += 2

    # ROE (higher is better)
    roe = fundamentals.get("ROE")
    if roe is not None:
        max_points += 15
        if roe > 0.20:
            score += 15
        elif roe > 0.15:
            score += 12
        elif roe > 0.10:
            score += 8
        elif roe > 0:
            score += 4
        else:
            score += 0

    # Debt/Equity (lower is better)
    de = fundamentals.get("DebtEquity")
    if de is not None:
        max_points += 15
        if de < 30:
            score += 15
        elif de < 80:
            score += 10
        elif de < 150:
            score += 5
        else:
            score += 1

    # Profit Margin (higher is better)
    pm = fundamentals.get("ProfitMargin")
    if pm is not None:
        max_points += 10
        if pm > 0.20:
            score += 10
        elif pm > 0.10:
            score += 7
        elif pm > 0.05:
            score += 4
        else:
            score += 1

    # Dividend Yield (moderate is good)
    dy = fundamentals.get("DividendYield")
    if dy is not None:
        max_points += 10
        if 0.01 < dy < 0.06:
            score += 10
        elif dy > 0:
            score += 5
        else:
            score += 3

    # P/B Ratio (lower is better)
    pb = fundamentals.get("PB")
    if pb is not None and pb > 0:
        max_points += 10
        if pb < 2:
            score += 10
        elif pb < 4:
            score += 7
        elif pb < 8:
            score += 4
        else:
            score += 1

    if max_points > 0:
        return round((score / max_points) * 100, 2)
    return 50.0


if __name__ == "__main__":
    from data_fetcher import fetch_ohlcv, fetch_fundamentals

    symbol = "RELIANCE"
    print(f"Calculating indicators for {symbol}...")
    
    ohlcv = fetch_ohlcv(symbol, "long_term")
    if not ohlcv.empty:
        with_indicators = calculate_all_indicators(ohlcv)
        print(f"Columns: {list(with_indicators.columns)}")
        print(f"\nTechnical Score: {generate_technical_score(with_indicators)}")
        
        fund = fetch_fundamentals(symbol)
        print(f"Fundamental Score: {generate_fundamental_score(fund)}")
