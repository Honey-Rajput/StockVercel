"""
Fetch 1000+ NSE stock symbols and create stocks.xlsx
Uses publicly available NSE stock lists.
"""
import os
import pandas as pd
import requests
import io

def fetch_nse_stocks():
    """Fetch all NSE equity stocks directly from NSE website."""
    
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    print("Fetching NSE equity list...")
    response = requests.get(url, headers=headers)
    
    # Read CSV
    df = pd.read_csv(io.StringIO(response.text))
    
    # Clean up column names (NSE CSV often has leading spaces)
    df.columns = df.columns.str.strip()
    
    # Filter for Series = EQ (Equities)
    if 'SERIES' in df.columns:
        df = df[df['SERIES'] == 'EQ']
    
    unique_stocks = []
    
    # Process dataframe
    for _, row in df.iterrows():
        # Fallback values if metadata isn't present
        symbol = str(row.get('SYMBOL', '')).strip()
        if not symbol:
            continue
            
        name = str(row.get('NAME OF COMPANY', symbol)).strip()
        
        unique_stocks.append({
            "Symbol": symbol,
            "Name": name,
            "Sector": "Unknown", # Can be enriched later
            "Market_Cap_Category": "Unknown", # Can be enriched later
        })

    return unique_stocks

def main():
    stocks = fetch_nse_stocks()
    df = pd.DataFrame(stocks)

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stocks.xlsx")
    df.to_excel(output_path, index=False)

    print(f"[OK] Created {output_path} with {len(df)} stocks")

if __name__ == "__main__":
    main()
