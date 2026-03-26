import os
import pandas as pd
import requests
import json
from config import NEON_DB_URL

# psycopg2 is imported here for any legacy direct queries, but we use HTTP for inserts

API_BASE_URL = "http://localhost:3000"

def get_connection():
    """Fallback connection if direct DB access is ever needed"""
    import psycopg2
    return psycopg2.connect(dsn=NEON_DB_URL)

def init_database():
    """Database initialization is now handled by Next.js /api/init-db"""
    pass 

def save_recommendations(results: dict):
    """
    Saves all recommendations over HTTP in 100-row chunks 
    to bypass strict local firewall rules & Next.js 1MB limits.
    """
    import math
    from datetime import datetime
    
    today_date = datetime.now().strftime('%Y-%m-%d')
    all_records = []
    
    for tf, df in results.items():
        if df.empty:
            continue
            
        for idx, row in df.iterrows():
            # Handle date format
            date_val = row.get("Date")
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime('%Y-%m-%d')
            else:
                date_str = str(date_val).split(" ")[0] if date_val else today_date
                
            rec = {
                "date": date_str,
                "timeframe": tf,
                "rank": idx if isinstance(idx, int) and idx > 0 else 1, # The index is usually Rank
                "symbol": row.get("Symbol"),
                "name": row.get("Name", ""),
                "sector": row.get("Sector", "Unknown"),
                "close": row.get("Close", 0.0),
                "change_pct": row.get("Change%", 0.0),
                "ml_score": row.get("ML_Score", 0.0),
                "tech_score": row.get("Tech_Score", 0.0),
                "fund_score": row.get("Fund_Score", 0.0),
                "composite_score": row.get("Composite_Score", 0.0),
                "signal": row.get("Signal", "Hold"),
                "entry_price": row.get("Entry", 0.0),
                "stop_loss": row.get("Stop_Loss", 0.0),
                "target_1": row.get("Target_1", 0.0),
                "target_2": row.get("Target_2", 0.0),
                "rsi": row.get("RSI", 0.0),
                "macd_hist": row.get("MACD_Hist", 0.0),
                "volume_ratio": row.get("Volume_Ratio", 1.0),
                "atr": row.get("ATR", 0.0),
                "pe": row.get("PE", None),
                "roe": row.get("ROE", None)
            }
            
            # Clean pure NaNs for JSON
            for k, v in rec.items():
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    rec[k] = None
                    
            all_records.append(rec)
            
    if not all_records:
        print("No records to save.")
        return
        
    try:
        # Clear previous records for today before inserting new batches to prevent duplicates
        today_date = all_records[0].get("date", "2026-03-25")
        res_clear = requests.post(f"{API_BASE_URL}/api/clear-results", json={"date": today_date}, timeout=15)
        if res_clear.status_code == 200:
            print("Cleared today's previous records to prevent duplicates.")
    except Exception as e:
        print(f"Failed to clear old records via API: {e}")
        
    batch_size = 100
    total_batches = (len(all_records) + batch_size - 1) // batch_size
    print(f"\nSaving {len(all_records)} recommendations to DB via API in {total_batches} batches...")
    
    success_count = 0
    for i in range(total_batches):
        batch = all_records[i * batch_size : (i + 1) * batch_size]
        try:
            batch_json = json.dumps({"recommendations": batch})
            response = requests.post(f"{API_BASE_URL}/api/save-results", data=batch_json, headers={"Content-Type": "application/json"}, timeout=30)
            if response.status_code == 200:
                success_count += len(batch)
            else:
                print(f"  ✗ API Error on batch {i+1}: {response.text}")
        except Exception as e:
            print(f"  ✗ Failed to communicate with DB API: {e}")
            
    print(f"✓ Successfully saved {success_count}/{len(all_records)} directly to cloud DB over HTTP API!")

def save_backtest_results(results: dict):
    # This can also be ported to HTTP later if needed
    pass

def get_historical_recommendations(symbol: str, limit: int = 5) -> pd.DataFrame:
    # Read-only queries can still use the direct DB if open, or return empty local dataframe
    return pd.DataFrame()

def get_stock_universe() -> list:
    return []
