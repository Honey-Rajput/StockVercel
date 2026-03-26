"""
Central Configuration for Automated Stock Recommendation System
"""
import os
from datetime import datetime

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

# ============================================================
# STOCK UNIVERSE
# ============================================================
STOCKS_FILE = os.path.join(os.path.dirname(__file__), "stocks.xlsx")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
HISTORY_DIR = os.path.join(OUTPUT_DIR, "history")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

# How many trading days of history to keep
HISTORY_DAYS = 5

# ============================================================
# DATA FETCHING
# ============================================================
# yfinance suffix for NSE stocks
NSE_SUFFIX = ".NS"

# Data periods for different strategies
DATA_PERIODS = {
    "intraday": {"period": "7d", "interval": "15m"},
    "short_term": {"period": "3mo", "interval": "1h"},
    "long_term": {"period": "1y", "interval": "1d"},
}

# Fundamental data cache duration (hours)
CACHE_DURATION_HOURS = 6

# ============================================================
# TECHNICAL INDICATORS
# ============================================================
SMA_PERIODS = [20, 50, 200]
EMA_PERIODS = [9, 21]
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BB_PERIOD = 20
BB_STD = 2
ATR_PERIOD = 14
ADX_PERIOD = 14
STOCH_PERIOD = 14
CCI_PERIOD = 20
WILLIAMS_PERIOD = 14

# ============================================================
# ML ENGINE
# ============================================================
# Forward return periods (in candles) for target calculation
FORWARD_RETURNS = {
    "intraday": 4,      # 4 x 15min = 1 hour ahead
    "short_term": 5,    # 5 x 1h ≈ 1 day ahead
    "long_term": 30,    # 30 x 1d = 30 days ahead
}

# ML hyperparameters
RF_PARAMS = {
    "n_estimators": 200,
    "max_depth": 10,
    "min_samples_split": 10,
    "min_samples_leaf": 5,
    "random_state": 42,
    "n_jobs": -1,
}

XGB_PARAMS = {
    "n_estimators": 200,
    "max_depth": 6,
    "learning_rate": 0.1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": 42,
    "verbosity": 0,
}

# Ensemble weights (RF, XGB)
ENSEMBLE_WEIGHTS = [0.4, 0.6]

# ============================================================
# SCORING WEIGHTS
# ============================================================
# Final score = ML_WEIGHT * ml_score + TECH_WEIGHT * tech_score + FUND_WEIGHT * fund_score
SCORING_WEIGHTS = {
    "intraday": {"ml": 0.5, "technical": 0.4, "fundamental": 0.1},
    "short_term": {"ml": 0.4, "technical": 0.3, "fundamental": 0.3},
    "long_term": {"ml": 0.3, "technical": 0.2, "fundamental": 0.5},
}

# ============================================================
# RECOMMENDATION THRESHOLDS
# ============================================================
SIGNAL_THRESHOLDS = {
    "strong_buy": 65,
    "buy": 50,
    "hold_upper": 47,
    "hold_lower": 40,
    "sell": 30,
    # Below 30 = Strong Sell
}

# ============================================================
# BACKTESTING
# ============================================================
BACKTEST_INITIAL_CAPITAL = 100000  # ₹1,00,000
BACKTEST_COMMISSION = 0.001  # 0.1% per trade
BACKTEST_SLIPPAGE = 0.001   # 0.1% slippage

# ============================================================
# PORTFOLIO ALLOCATION
# ============================================================
RISK_PROFILES = {
    "conservative": {
        "max_stocks": 8,
        "max_sector_pct": 0.25,
        "stop_loss_atr_mult": 2.0,
        "target_atr_mult": 3.0,
        "max_single_stock_pct": 0.15,
    },
    "moderate": {
        "max_stocks": 12,
        "max_sector_pct": 0.30,
        "stop_loss_atr_mult": 1.5,
        "target_atr_mult": 4.0,
        "max_single_stock_pct": 0.12,
    },
    "aggressive": {
        "max_stocks": 15,
        "max_sector_pct": 0.40,
        "stop_loss_atr_mult": 1.0,
        "target_atr_mult": 5.0,
        "max_single_stock_pct": 0.10,
    },
}

# ============================================================
# SCHEDULER
# ============================================================
# IST times for daily runs
SCHEDULE_TIMES = {
    "pre_market": "08:45",    # Before market open
    "mid_day": "12:30",       # Mid-day update
    "post_market": "15:45",   # After market close
}

TIMEZONE = "Asia/Kolkata"

# ============================================================
# ALERTS
# ============================================================
# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# WhatsApp (Twilio)
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
TWILIO_WHATSAPP_TO = os.environ.get("TWILIO_WHATSAPP_TO", "whatsapp:+91XXXXXXXXXX")

# WhatsApp (pywhatkit fallback)
PYWHATKIT_PHONE = os.environ.get("PYWHATKIT_PHONE", "+91XXXXXXXXXX")

# Alert mode: "telegram", "whatsapp_twilio", "whatsapp_pywhatkit", "all"
ALERT_MODE = os.environ.get("ALERT_MODE", "telegram")

# ============================================================
# NEON DB (Serverless Postgres)
# ============================================================
NEON_DB_URL = os.environ.get("DATABASE_URL", "")

# ============================================================
# PATHS SETUP
# ============================================================
for d in [OUTPUT_DIR, HISTORY_DIR, MODELS_DIR]:
    os.makedirs(d, exist_ok=True)
