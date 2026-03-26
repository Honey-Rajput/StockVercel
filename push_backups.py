import os
import pandas as pd
import requests
import json
import numpy as np
import datetime

API_BASE_URL = "http://localhost:3000"

def push_data():
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    files = [f for f in os.listdir(output_dir) if f.startswith("recommendations_") and f.endswith(".xlsx")]
    if not files:
        print("No recommendations file found.")
        return
        
    latest_file = sorted(files)[-1]
    xls = pd.ExcelFile(os.path.join(output_dir, latest_file))
    print(f"Loading {latest_file}...")
    
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    all_records = []
    
    for sheet in xls.sheet_names:
        tf_key = sheet.lower().replace(" ", "_")
        df = pd.read_excel(xls, sheet_name=sheet)
        
        # Replace NaN/Inf with None
        df = df.replace([np.inf, -np.inf], None)
        df = df.where(pd.notna(df), None)
        
        for idx, row in df.iterrows():
            # Handle date format
            date_str = today_str
                
            rec = {
                "date": date_str,
                "timeframe": tf_key,
                "rank": idx + 1,
                "symbol": row.get("Symbol"),
                "name": row.get("Name"),
                "sector": row.get("Sector"),
                "close": row.get("Close"),
                "change_pct": row.get("Change%"),
                "ml_score": row.get("ML_Score"),
                "tech_score": row.get("Tech_Score"),
                "fund_score": row.get("Fund_Score"),
                "composite_score": row.get("Composite_Score"),
                "signal": row.get("Signal"),
                "entry_price": row.get("Entry"),
                "stop_loss": row.get("Stop_Loss"),
                "target_1": row.get("Target_1"),
                "target_2": row.get("Target_2"),
                "rsi": row.get("RSI"),
                "macd_hist": row.get("MACD_Hist"),
                "volume_ratio": row.get("Volume_Ratio"),
                "atr": row.get("ATR"),
                "pe": row.get("PE"),
                "roe": row.get("ROE")
            }
            # Clean NaNs
            import math
            for k, v in rec.items():
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    rec[k] = None
            all_records.append(rec)
            
    print(f"Total mapped records across all timeframes: {len(all_records)}")
    
    # Push in batches of 100
    batch_size = 100
    total_batches = (len(all_records) + batch_size - 1) // batch_size
    
    print(f"Pushing {len(all_records)} records in {total_batches} batches...")
    
    success_count = 0
    for i in range(total_batches):
        batch = all_records[i * batch_size : (i + 1) * batch_size]
        try:
            # We use data and stringify it manually to avoid requests json parser issues
            import json
            batch_json = json.dumps({"recommendations": batch})
            res = requests.post(
                f"{API_BASE_URL}/api/save-results", 
                data=batch_json, 
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            if res.status_code == 200:
                print(f" Batch {i+1}/{total_batches} successful.")
                success_count += len(batch)
            else:
                print(f" Batch {i+1}/{total_batches} failed: {res.text}")
        except Exception as e:
            print(f" Error on batch {i+1}: {str(e)}")
            
    print(f"\nDone! Successfully pushed {success_count}/{len(all_records)} records to Neon DB.")

if __name__ == "__main__":
    push_data()
