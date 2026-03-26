"""
Recommendation Engine Module
Combines ML, technical, and fundamental scores to generate ranked recommendations.
"""
import os
import shutil
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

import config
from data_fetcher import load_stock_universe, fetch_all_data
from technical_indicators import calculate_all_indicators, generate_technical_score, generate_fundamental_score
from ml_engine import batch_predict


def _classify_signal(score: float) -> str:
    """Convert numeric score to signal label."""
    if score >= config.SIGNAL_THRESHOLDS["strong_buy"]:
        return "🟢 Strong Buy"
    elif score >= config.SIGNAL_THRESHOLDS["buy"]:
        return "🔵 Buy"
    elif score >= config.SIGNAL_THRESHOLDS["hold_upper"]:
        return "🟡 Hold"
    elif score >= config.SIGNAL_THRESHOLDS["hold_lower"]:
        return "🟡 Hold"
    elif score >= config.SIGNAL_THRESHOLDS["sell"]:
        return "🟠 Sell"
    else:
        return "🔴 Strong Sell"


def _calculate_targets(last_close: float, atr: float, signal: str):
    """Calculate entry, stop-loss, and target prices dynamically based on signal direction."""
    entry = last_close
    
    if "Sell" in signal:
        # For Short positions, target is LOWER, stop-loss is HIGHER
        stop_loss = round(entry + (1.5 * atr), 2)
        target_1 = round(entry - (2.0 * atr), 2)
        target_2 = round(entry - (3.5 * atr), 2)
    else:
        # Standard Long positions
        stop_loss = round(entry - (1.5 * atr), 2)
        target_1 = round(entry + (2.0 * atr), 2)
        target_2 = round(entry + (3.5 * atr), 2)
        
    return entry, stop_loss, target_1, target_2


def generate_recommendations(timeframe: str = "long_term") -> pd.DataFrame:
    """
    Full pipeline: load stocks → fetch data → indicators → ML → score → rank.
    
    Returns:
        DataFrame with ranked recommendations
    """
    print(f"\n{'='*60}")
    print(f"  Generating {timeframe.upper()} recommendations")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    # 1. Load stock universe
    stocks_df = load_stock_universe()
    symbols = stocks_df["Symbol"].tolist()
    stock_info = stocks_df.set_index("Symbol").to_dict("index")

    print(f"\n📋 {len(symbols)} stocks loaded")

    # 2. Fetch data
    print(f"\n📡 Fetching {timeframe} data...")
    with_fundamentals = timeframe != "intraday"  # Skip fundamentals for intraday speed
    all_data = fetch_all_data(symbols, timeframe, with_fundamentals)

    if not all_data:
        print("  ✗ No data fetched!")
        return pd.DataFrame()

    # 3. Calculate technical indicators
    print(f"\n📊 Calculating technical indicators...")
    try:
        import json
        with open(os.path.join(os.path.dirname(__file__), "progress.json"), "w") as f:
            json.dump({"current": len(symbols), "total": len(symbols), "status": "Calculating Technical Indicators...", "phase": f"Processing ({timeframe})"}, f)
    except: pass
    
    for symbol in all_data:
        try:
            res = calculate_all_indicators(all_data[symbol]["ohlcv"])
            if not res.empty:
                all_data[symbol]["ohlcv"] = res
        except Exception:
            pass

    # 4. ML scoring
    print(f"\n🤖 Running ML predictions...")
    try:
        import json
        with open(os.path.join(os.path.dirname(__file__), "progress.json"), "w") as f:
            json.dump({"current": len(symbols), "total": len(symbols), "status": "Running Random Forest & XGBoost Models...", "phase": f"ML Scoring ({timeframe})"}, f)
    except: pass
    
    ml_scores = batch_predict(all_data, timeframe)

    # 5. Build recommendation table
    print(f"\n📝 Building recommendations...")
    try:
        import json
        with open(os.path.join(os.path.dirname(__file__), "progress.json"), "w") as f:
            json.dump({"current": len(symbols), "total": len(symbols), "status": "Finalizing Ranks and Composite Scores...", "phase": f"Ranking ({timeframe})"}, f)
    except: pass
    weights = config.SCORING_WEIGHTS[timeframe]
    rows = []

    for symbol, data in all_data.items():
        ohlcv = data["ohlcv"]
        fundamentals = data.get("fundamentals", {})

        if ohlcv.empty or len(ohlcv) < 5:
            continue

        try:
            last = ohlcv.iloc[-1]
            
            # Safe float extraction (handles Series from multi-level columns)
            def safe_float(val, default=0.0):
                try:
                    if hasattr(val, 'iloc'):
                        val = val.iloc[0]
                    return float(val) if val is not None and not pd.isna(val) else default
                except (TypeError, ValueError):
                    return default
            
            last_close = safe_float(last["Close"])
            if last_close <= 0:
                continue
            atr = safe_float(last.get("ATR", last_close * 0.02))
            if atr <= 0:
                atr = last_close * 0.02

            # Individual scores
            ml_score = ml_scores.get(symbol, 50.0)
            tech_score = generate_technical_score(ohlcv)
            fund_score = generate_fundamental_score(fundamentals) if fundamentals else 50.0

            # Weighted composite score
            composite = (
                weights["ml"] * ml_score +
                weights["technical"] * tech_score +
                weights["fundamental"] * fund_score
            )
            composite = round(composite, 2)
            
            signal_str = _classify_signal(composite)
            entry, stop_loss, target_1, target_2 = _calculate_targets(last_close, atr, signal_str)

            info = stock_info.get(symbol, {})

            rows.append({
                "Symbol": symbol,
                "Name": info.get("Name", symbol),
                "Sector": info.get("Sector", "Unknown"),
                "Close": round(last_close, 2),
                "Change%": round(safe_float(last.get("Return_1d", 0)) * 100, 2),
                "ML_Score": ml_score,
                "Tech_Score": tech_score,
                "Fund_Score": fund_score,
                "Composite_Score": composite,
                "Signal": signal_str,
                "Entry": entry,
                "Stop_Loss": stop_loss,
                "Target_1": target_1,
                "Target_2": target_2,
                "RSI": round(safe_float(last.get("RSI", 50)), 2),
                "MACD_Hist": round(safe_float(last.get("MACD_Hist", 0)), 4),
                "Volume_Ratio": round(safe_float(last.get("Volume_Ratio", 1)), 2),
                "ATR": round(atr, 2),
                "PE": fundamentals.get("PE"),
                "ROE": fundamentals.get("ROE"),
            })
        except Exception:
            continue

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Sort by composite score (highest first)
    df = df.sort_values("Composite_Score", ascending=False).reset_index(drop=True)
    df.index = df.index + 1  # 1-based ranking
    df.index.name = "Rank"

    print(f"  ✓ {len(df)} stocks ranked")
    return df


def run_full_analysis() -> dict:
    """
    Run analysis for all 3 timeframes and return results.
    
    Returns:
        dict: {"intraday": df, "short_term": df, "long_term": df}
    """
    import traceback
    results = {}
    for tf in ["intraday", "short_term", "long_term"]:
        try:
            results[tf] = generate_recommendations(tf)
        except Exception as e:
            print(f"  ✗ Error in {tf}: {e}")
            traceback.print_exc()
            results[tf] = pd.DataFrame()
    return results


def save_results(results: dict) -> str:
    """
    Save results to Excel (today's file + history).
    Returns the output file path.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    output_file = os.path.join(config.OUTPUT_DIR, f"recommendations_{today}.xlsx")

    # Check if there's any data to write
    has_data = any(not df.empty for df in results.values())
    if not has_data:
        print("  ⚠ No data to save - all timeframes returned empty results")
        return output_file

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        for tf, df in results.items():
            if not df.empty:
                sheet_name = tf.replace("_", " ").title()
                df.to_excel(writer, sheet_name=sheet_name)

    print(f"\n💾 Saved to: {output_file}")

    # Save to Neon DB (if configured)
    try:
        from database import save_recommendations, NEON_DB_URL
        if NEON_DB_URL and "user:password" not in NEON_DB_URL:
            save_recommendations(results)
        else:
            print("  ⚠ Neon DB not configured, skipping DB save")
    except Exception as e:
        print(f"  ⚠ DB save skipped: {e}")

    # Copy to history
    history_file = os.path.join(config.HISTORY_DIR, f"recommendations_{today}.xlsx")
    shutil.copy2(output_file, history_file)

    # Cleanup old history (keep only last N trading days)
    _cleanup_history()

    return output_file


def _cleanup_history():
    """Keep only the last HISTORY_DAYS files in history directory."""
    files = sorted(
        [f for f in os.listdir(config.HISTORY_DIR) if f.endswith(".xlsx")],
        reverse=True
    )
    for old_file in files[config.HISTORY_DAYS:]:
        os.remove(os.path.join(config.HISTORY_DIR, old_file))
        print(f"  🗑 Removed old history: {old_file}")


def load_history() -> dict:
    """
    Load all history files.
    
    Returns:
        dict: {date_str: {"intraday": df, "short_term": df, "long_term": df}}
    """
    history = {}
    if not os.path.exists(config.HISTORY_DIR):
        return history

    for fname in sorted(os.listdir(config.HISTORY_DIR)):
        if not fname.endswith(".xlsx"):
            continue
        date_str = fname.replace("recommendations_", "").replace(".xlsx", "")
        fpath = os.path.join(config.HISTORY_DIR, fname)

        try:
            xls = pd.ExcelFile(fpath)
            day_data = {}
            for sheet in xls.sheet_names:
                tf_key = sheet.lower().replace(" ", "_")
                day_data[tf_key] = pd.read_excel(xls, sheet_name=sheet, index_col=0)
            history[date_str] = day_data
        except Exception:
            pass

    return history


if __name__ == "__main__":
    results = run_full_analysis()
    save_results(results)

    for tf, df in results.items():
        if not df.empty:
            print(f"\n{'='*40}")
            print(f"  TOP 5 — {tf.upper()}")
            print(f"{'='*40}")
            print(df[["Symbol", "Close", "Composite_Score", "Signal"]].head())
