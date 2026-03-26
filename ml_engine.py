"""
ML Engine Module
Random Forest + XGBoost ensemble for stock scoring.
"""
import os
import warnings
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
import xgboost as xgb
import joblib

import config

warnings.filterwarnings("ignore")

# Features to use for ML model
FEATURE_COLS = [
    "RSI", "MACD", "MACD_Hist", "ADX", "ADX_Pos", "ADX_Neg",
    "Stoch_K", "Stoch_D", "Williams_R", "CCI", "ROC",
    "BB_PctB", "BB_Width", "ATR",
    "OBV", "Volume_Ratio",
    "Price_vs_SMA20", "Price_vs_SMA50",
    "Return_1d", "Return_5d", "Return_10d", "Return_20d",
    "Volatility_20d", "Price_Position",
]

# Additional fundamental features added at scoring time
FUNDAMENTAL_FEATURES = ["PE", "PB", "ROE", "DebtEquity", "DividendYield", "Beta", "ProfitMargin"]


def _prepare_features(df: pd.DataFrame, fundamentals: dict = None) -> pd.DataFrame:
    """Select and clean feature columns."""
    available = [c for c in FEATURE_COLS if c in df.columns]
    features = df[available].copy()

    # Add fundamental features as constant columns if available
    if fundamentals:
        for feat in FUNDAMENTAL_FEATURES:
            val = fundamentals.get(feat)
            if val is not None and not pd.isna(val):
                features[feat] = float(val)

    # Forward fill then fill remaining NaNs with 0 to prevent dropping entire intraday sets
    features = features.ffill().fillna(0)
    return features


def _create_target(df: pd.DataFrame, forward_period: int) -> pd.Series:
    """
    Create binary target: 1 if forward return > 0, else 0.
    """
    forward_return = df["Close"].pct_change(forward_period).shift(-forward_period)
    target = (forward_return > 0).astype(int)
    target.name = "Target"
    return target


def train_model(df: pd.DataFrame, timeframe: str, fundamentals: dict = None):
    """
    Train RF + XGBoost ensemble on the given data.
    
    Returns:
        tuple: (rf_model, xgb_model, scaler, feature_names)
    """
    forward_period = config.FORWARD_RETURNS[timeframe]
    
    features = _prepare_features(df, fundamentals)
    target = _create_target(df, forward_period)

    # Align features and target
    common_idx = features.index.intersection(target.dropna().index)
    X = features.loc[common_idx]
    y = target.loc[common_idx]

    if len(X) < 20:
        return None, None, None, None

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train Random Forest
    rf = RandomForestClassifier(**config.RF_PARAMS)
    rf.fit(X_scaled, y)

    # Train XGBoost
    xgb_model = xgb.XGBClassifier(**config.XGB_PARAMS)
    xgb_model.fit(X_scaled, y)

    return rf, xgb_model, scaler, list(X.columns)


def predict_score(df: pd.DataFrame, timeframe: str, fundamentals: dict = None) -> float:
    """
    Train on historical data and predict the ML score (0-100) for the latest candle.
    
    Returns:
        float: Score 0-100 (higher = more bullish)
    """
    rf, xgb_model, scaler, feature_names = train_model(df, timeframe, fundamentals)

    if rf is None:
        return 50.0  # Neutral if not enough data

    # Prepare the latest data point
    features = _prepare_features(df, fundamentals)
    if features.empty:
        return 50.0

    latest = features.iloc[[-1]]

    # Ensure same columns as training
    for col in feature_names:
        if col not in latest.columns:
            latest[col] = 0
    latest = latest[feature_names]

    latest_scaled = scaler.transform(latest)

    # Get probability of positive return
    rf_prob = rf.predict_proba(latest_scaled)[0][1]
    xgb_prob = xgb_model.predict_proba(latest_scaled)[0][1]

    # Ensemble
    ensemble_prob = (
        config.ENSEMBLE_WEIGHTS[0] * rf_prob +
        config.ENSEMBLE_WEIGHTS[1] * xgb_prob
    )

    # Convert to 0-100 score
    score = round(ensemble_prob * 100, 2)
    return score


def batch_predict(all_data: dict, timeframe: str) -> dict:
    """
    Run ML prediction for all stocks using a single unified model per timeframe.
    Extremely fast compared to per-stock training.
    """
    scores = {}
    total = len(all_data)
    
    if total == 0:
        return {}

    print(f"  🤖 Training unified ML model for {timeframe}...")
    
    # 1. Prepare a pooled training set from multiple stocks for better generalization
    # (Using up to 50 stocks to build a robust general model)
    pooled_X = []
    pooled_y = []
    training_symbols = list(all_data.keys())[:50] 
    forward_period = config.FORWARD_RETURNS[timeframe]

    for sym in training_symbols:
        df = all_data[sym]["ohlcv"]
        fund = all_data[sym].get("fundamentals", {})
        
        features = _prepare_features(df, fund)
        target = _create_target(df, forward_period)
        
        common_idx = features.index.intersection(target.dropna().index)
        if len(common_idx) > 10:
            pooled_X.append(features.loc[common_idx])
            pooled_y.append(target.loc[common_idx])

    if not pooled_X:
        print("    ⚠ Not enough pooling data. Using neutral scores.")
        return {sym: 50.0 for sym in all_data}

    X_train = pd.concat(pooled_X, ignore_index=True)
    y_train = pd.concat(pooled_y, ignore_index=True)
    
    # 2. Train the unified model
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)
    
    rf = RandomForestClassifier(**config.RF_PARAMS)
    rf.fit(X_scaled, y_train)
    
    xgb_model = xgb.XGBClassifier(**config.XGB_PARAMS)
    xgb_model.fit(X_scaled, y_train)
    
    feature_names = list(X_train.columns)
    
    # 3. Apply to all stocks
    print(f"  🚀 Scoring {total} stocks with unified model...")
    for i, (symbol, data) in enumerate(all_data.items(), 1):
        try:
            features = _prepare_features(data["ohlcv"], data.get("fundamentals", {}))
            if features.empty:
                scores[symbol] = 50.0
                continue
                
            latest = features.iloc[[-1]]
            # Ensure columns match training
            for col in feature_names:
                if col not in latest.columns:
                    latest[col] = 0
            latest = latest[feature_names]
            
            latest_scaled = scaler.transform(latest)
            rf_prob = rf.predict_proba(latest_scaled)[0][1]
            xgb_prob = xgb_model.predict_proba(latest_scaled)[0][1]
            
            prob = (config.ENSEMBLE_WEIGHTS[0] * rf_prob + config.ENSEMBLE_WEIGHTS[1] * xgb_prob)
            scores[symbol] = round(prob * 100, 2)
        except Exception:
            scores[symbol] = 50.0
            
    return scores


if __name__ == "__main__":
    from data_fetcher import fetch_ohlcv, fetch_fundamentals
    from technical_indicators import calculate_all_indicators

    symbol = "RELIANCE"
    print(f"ML scoring for {symbol}...")

    ohlcv = fetch_ohlcv(symbol, "long_term")
    if not ohlcv.empty:
        df = calculate_all_indicators(ohlcv)
        fund = fetch_fundamentals(symbol)
        
        for tf in ["long_term", "short_term"]:
            score = predict_score(df, tf, fund)
            print(f"  {tf}: {score}/100")
