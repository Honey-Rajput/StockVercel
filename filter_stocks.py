"""
Filter stocks.xlsx: Keep ONLY stocks with price >= 30 AND market cap >= 1000 Crore.
Also enriches Sector and Market Cap columns (currently 'Unknown').
Saves backup of original file before overwriting.
"""
import os
import sys
import time
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed

STOCKS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stocks.xlsx")
BACKUP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stocks_backup_full.xlsx")
MIN_PRICE = 30.0
MIN_MARKET_CAP = 10_000_000_000  # 1000 Crore = 10 Billion INR


def get_mcap_and_sector(symbol):
    """Check a single stock's market cap and sector."""
    try:
        t = yf.Ticker(f"{symbol}.NS")
        
        mcap = None
        try:
            mcap = t.fast_info.get("market_cap")
        except Exception:
            try:
                mcap = t.info.get("marketCap")
            except Exception:
                pass
                
        sector = "Unknown"
        try:
            sector = t.info.get("sector", "Unknown")
        except Exception:
            pass
            
        return {
            "symbol": symbol,
            "mcap": float(mcap) if mcap else None,
            "sector": sector or "Unknown",
            "mcap_cr": round(float(mcap) / 1e7, 0) if mcap else None,
        }
    except Exception as e:
        return {"symbol": symbol, "mcap": None, "sector": "Unknown", "mcap_cr": None}


def filter_stocks():
    df = pd.read_excel(STOCKS_FILE)
    df.columns = [c.strip() for c in df.columns]
    original_count = len(df)
    symbols = df["Symbol"].tolist()
    
    print(f"Original: {original_count} stocks")
    print(f"Phase 1: Batch fetching latest prices to filter (< Rs.30)...")
    
    # 1. Batch download prices
    tickers = [f"{sym}.NS" for sym in symbols]
    batch_size = 500
    prices = {}
    
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        batch_syms = symbols[i:i+batch_size]
        print(f"  Fetching batch {i//batch_size + 1}...")
        try:
            data = yf.download(batch, period="5d", progress=False, threads=True, auto_adjust=False)
            
            for sym, ticker in zip(batch_syms, batch):
                try:
                    if isinstance(data.columns, pd.MultiIndex):
                        if ticker in data["Close"].columns:
                            close = data["Close"][ticker].dropna().iloc[-1]
                            prices[sym] = float(close)
                    else:
                        close = data["Close"].dropna().iloc[-1]
                        prices[sym] = float(close)
                except Exception:
                    prices[sym] = None
        except Exception as e:
            print(f"  Batch error: {e}")
            
    # Filter by price first
    price_passed = []
    removed_price = 0
    for sym in symbols:
        p = prices.get(sym)
        if p is not None and p >= MIN_PRICE:
            price_passed.append(sym)
        elif p is not None and p < MIN_PRICE:
            removed_price += 1
        else:
            # If we couldn't fetch price, keep it to be safe (e.g. RELIANCE)
            price_passed.append(sym)
            
    print(f"Passed price check: {len(price_passed)} stocks")
    print(f"\nPhase 2: Fetching Market Cap (>= 1000Cr) via threads...")
    
    results = {}
    completed = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_mcap_and_sector, sym): sym for sym in price_passed}
        for future in as_completed(futures):
            completed += 1
            res = future.result()
            results[res["symbol"]] = res
            if completed % 100 == 0:
                sys.stdout.write(f"  Checked {completed}/{len(price_passed)}...\r")
                sys.stdout.flush()
    print(f"  Checked {completed}/{len(price_passed)}... Done")
    
    # Apply filters
    kept = []
    removed_mcap = 0
    
    for _, row in df.iterrows():
        sym = row["Symbol"]
        if sym not in price_passed:
            continue
            
        info = results.get(sym, {})
        mcap = info.get("mcap")
        
        # Keep if mcap >= threshold, or if we couldn't fetch it (fail-open)
        if mcap is not None and mcap < MIN_MARKET_CAP:
            removed_mcap += 1
            continue
            
        kept.append({
            "Symbol": sym,
            "Name": row.get("Name", sym),
            "Sector": info.get("sector", "Unknown"),
            "Market_Cap_Cr": info.get("mcap_cr", 0) if info.get("mcap_cr") else 0,
        })
    
    filtered_df = pd.DataFrame(kept)
    if "Market_Cap_Cr" in filtered_df.columns:
        filtered_df = filtered_df.sort_values("Market_Cap_Cr", ascending=False).reset_index(drop=True)
    
    if not os.path.exists(BACKUP_FILE):
        df.to_excel(BACKUP_FILE, index=False)
        print(f"\nBackup saved: {BACKUP_FILE}")
    
    filtered_df.to_excel(STOCKS_FILE, index=False)
    print(f"\n{'='*55}")
    print(f"  Original stocks:          {original_count}")
    print(f"  Removed (price < Rs.30):  {removed_price}")
    print(f"  Removed (mcap < 1000Cr):  {removed_mcap}")
    print(f"  KEPT (final):             {len(filtered_df)}")
    print(f"{'='*55}")
    print(f"\n  Saved to: {STOCKS_FILE}")

if __name__ == "__main__":
    filter_stocks()
