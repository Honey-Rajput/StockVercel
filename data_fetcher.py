"""
Data Fetcher Module
Fetches OHLCV + fundamental data from yfinance for NSE stocks.
"""
import os
import json
import time
import hashlib
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import yfinance as yf

import config


def _cache_path(symbol: str, timeframe: str) -> str:
    """Get cache file path for a symbol/timeframe combo."""
    cache_dir = os.path.join(config.OUTPUT_DIR, ".cache")
    os.makedirs(cache_dir, exist_ok=True)
    key = hashlib.md5(f"{symbol}_{timeframe}".encode()).hexdigest()
    return os.path.join(cache_dir, f"{key}.json")


def _is_cache_valid(cache_file: str) -> bool:
    """Check if cache file is still within validity window."""
    if not os.path.exists(cache_file):
        return False
    mod_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
    return (datetime.now() - mod_time).total_seconds() < config.CACHE_DURATION_HOURS * 3600


def load_stock_universe() -> pd.DataFrame:
    """Load stock list from stocks.xlsx."""
    df = pd.read_excel(config.STOCKS_FILE)
    df.columns = [c.strip() for c in df.columns]
    return df


def fetch_ohlcv(symbol: str, timeframe: str = "long_term") -> pd.DataFrame:
    """
    Fetch OHLCV data for a given symbol and timeframe.
    
    Args:
        symbol: Stock ticker (without .NS suffix)
        timeframe: 'intraday', 'short_term', or 'long_term'
    
    Returns:
        DataFrame with OHLCV columns
    """
    ticker = f"{symbol}{config.NSE_SUFFIX}"
    params = config.DATA_PERIODS[timeframe]

    try:
        data = yf.download(
            ticker,
            period=params["period"],
            interval=params["interval"],
            progress=False,
            auto_adjust=True,
        )

        if data.empty:
            print(f"  ⚠ No data for {symbol} ({timeframe})")
            return pd.DataFrame()

        # Flatten multi-level columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        # Remove duplicate columns (yfinance sometimes returns duplicates)
        data = data.loc[:, ~data.columns.duplicated()]

        data = data.dropna()
        data = data.reset_index(drop=False)  # Ensure unique index
        data.index = range(len(data))  # Clean integer index
        data.index.name = None
        return data

    except Exception as e:
        print(f"  ✗ Error fetching {symbol} ({timeframe}): {e}")
        return pd.DataFrame()


def fetch_fundamentals(symbol: str) -> dict:
    """
    Fetch fundamental ratios for a stock.

    Returns dict with: PE, PB, ROE, DebtEquity, DividendYield, MarketCap, 
                        BookValue, EPS, Revenue, ProfitMargin
    """
    cache_file = _cache_path(symbol, "fundamentals")

    if _is_cache_valid(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)

    ticker = yf.Ticker(f"{symbol}{config.NSE_SUFFIX}")
    info = ticker.info or {}

    fundamentals = {
        "PE": info.get("trailingPE", None),
        "PB": info.get("priceToBook", None),
        "ROE": info.get("returnOnEquity", None),
        "DebtEquity": info.get("debtToEquity", None),
        "DividendYield": info.get("dividendYield", None),
        "MarketCap": info.get("marketCap", None),
        "BookValue": info.get("bookValue", None),
        "EPS": info.get("trailingEps", None),
        "Revenue": info.get("totalRevenue", None),
        "ProfitMargin": info.get("profitMargins", None),
        "52WeekHigh": info.get("fiftyTwoWeekHigh", None),
        "52WeekLow": info.get("fiftyTwoWeekLow", None),
        "Beta": info.get("beta", None),
    }

    # Cache the result
    try:
        with open(cache_file, "w") as f:
            json.dump(fundamentals, f)
    except Exception:
        pass

    return fundamentals


from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_all_data(symbols: list, timeframe: str = "long_term", 
                   with_fundamentals: bool = True) -> dict:
    """
    Fetch OHLCV (and optionally fundamentals) for multiple symbols.
    Uses batch yf.download() to avoid yfinance multithreading bugs and rate limits.
    """
    all_data = {}
    total = len(symbols)
    params = config.DATA_PERIODS[timeframe]
    batch_size = 500
    
    print(f"  🚀 Batch downloading {total} stocks for {timeframe}...")

    completed = 0
    for i in range(0, total, batch_size):
        batch_syms = symbols[i:i+batch_size]
        tickers = [f"{sym}{config.NSE_SUFFIX}" for sym in batch_syms]
        
        try:
            data = yf.download(
                tickers,
                period=params["period"],
                interval=params["interval"],
                progress=False,
                threads=True,
                auto_adjust=False  # Safer for batch downloads
            )
            
            for sym in batch_syms:
                ticker = f"{sym}{config.NSE_SUFFIX}"
                df = pd.DataFrame()
                
                try:
                    if isinstance(data.columns, pd.MultiIndex):
                        if ticker in data.columns.get_level_values(1):
                            df["Open"] = data["Open"][ticker]
                            df["High"] = data["High"][ticker]
                            df["Low"] = data["Low"][ticker]
                            df["Close"] = data["Close"][ticker]
                            # Handle Adj Close if autoadjust is false
                            if "Adj Close" in data:
                                df["Close"] = data["Adj Close"][ticker] 
                            df["Volume"] = data["Volume"][ticker]
                    else:
                        if len(batch_syms) == 1:
                            df = data.copy()
                            if "Adj Close" in df.columns:
                                df["Close"] = df["Adj Close"]
                except Exception:
                    pass
                
                df = df.dropna()
                
                if not df.empty:
                    df = df.reset_index(drop=False)
                    if "Date" not in df.columns:
                        if "Datetime" in df.columns:
                            df.rename(columns={"Datetime": "Date"}, inplace=True)
                        elif "index" in df.columns:
                            df.rename(columns={"index": "Date"}, inplace=True)
                    
                    df.index = range(len(df))
                    df.index.name = None
                    all_data[sym] = {"ohlcv": df}
                    
        except Exception as e:
            print(f"  ✗ Error in OHLCV batch {i//batch_size + 1}: {e}")
            
        completed += len(batch_syms)
        try:
            with open(os.path.join(os.path.dirname(__file__), "progress.json"), "w") as f:
                json.dump({
                    "current": completed,
                    "total": total,
                    "status": f"Batch Fetching... ({completed}/{total})",
                    "phase": f"Fetching Data ({timeframe})"
                }, f)
        except Exception:
            pass

    # Fetch fundamentals concurrently (these don't suffer the same mixup bug if done carefully)
    if with_fundamentals:
        def fetch_fund_worker(sym):
            try:
                fund = fetch_fundamentals(sym)
                return sym, fund
            except Exception:
                return sym, {}
                
        print(f"  📊 Fetching fundamentals for {len(all_data)} stocks...")
        with ThreadPoolExecutor(max_workers=5) as executor:
            valid_syms = list(all_data.keys())
            futures = {executor.submit(fetch_fund_worker, sym): sym for sym in valid_syms}
            
            for future in as_completed(futures):
                sym, fund = future.result()
                if sym in all_data:
                    all_data[sym]["fundamentals"] = fund

    print(f"  ✓ Fetched data for {len(all_data)}/{total} stocks completely")
    return all_data


if __name__ == "__main__":
    # Quick test
    stocks = load_stock_universe()
    print(f"Loaded {len(stocks)} stocks from {config.STOCKS_FILE}")
    print(stocks.head())

    # Test single stock fetch
    test_symbol = stocks["Symbol"].iloc[0]
    print(f"\nFetching {test_symbol}...")
    data = fetch_ohlcv(test_symbol, "long_term")
    print(data.tail())
    
    fund = fetch_fundamentals(test_symbol)
    print(f"\nFundamentals: {fund}")
