"""
Backtesting Engine
Simulates trades using historical signals and calculates performance metrics.
"""
import pandas as pd
import numpy as np

import config
from data_fetcher import fetch_ohlcv
from technical_indicators import calculate_all_indicators, generate_technical_score


def backtest_stock(symbol: str, timeframe: str = "long_term",
                   initial_capital: float = None,
                   buy_threshold: float = 65,
                   sell_threshold: float = 45) -> dict:
    """
    Run a backtest on a single stock using technical score signals.
    
    Args:
        symbol: Stock ticker
        timeframe: Data timeframe
        initial_capital: Starting capital (₹)
        buy_threshold: Score above which to buy
        sell_threshold: Score below which to sell
    
    Returns:
        dict with backtest results + equity curve DataFrame
    """
    if initial_capital is None:
        initial_capital = config.BACKTEST_INITIAL_CAPITAL

    ohlcv = fetch_ohlcv(symbol, timeframe)
    if ohlcv.empty or len(ohlcv) < 60:
        return {"error": f"Not enough data for {symbol}"}

    df = calculate_all_indicators(ohlcv)
    df = df.dropna(subset=["RSI", "MACD_Hist"]).copy()

    if len(df) < 30:
        return {"error": "Not enough data after indicators"}

    # Calculate rolling technical scores
    scores = []
    for i in range(20, len(df)):
        window = df.iloc[:i+1]
        score = generate_technical_score(window)
        scores.append(score)

    df = df.iloc[20:].copy()
    df["Tech_Score"] = scores

    # Simulate trades
    capital = initial_capital
    shares = 0
    position = False
    trades = []
    equity_curve = []

    commission = config.BACKTEST_COMMISSION
    slippage = config.BACKTEST_SLIPPAGE

    for idx, row in df.iterrows():
        close = float(row["Close"])
        score = row["Tech_Score"]
        portfolio_value = capital + shares * close

        # Entry signal
        if not position and score >= buy_threshold:
            buy_price = close * (1 + slippage)
            cost = buy_price * (1 + commission)
            shares = int(capital * 0.95 / cost)  # Use 95% of capital
            if shares > 0:
                capital -= shares * cost
                position = True
                trades.append({
                    "Date": idx, "Type": "BUY", "Price": round(buy_price, 2),
                    "Shares": shares, "Value": round(shares * buy_price, 2)
                })

        # Exit signal
        elif position and score <= sell_threshold:
            sell_price = close * (1 - slippage)
            proceeds = sell_price * (1 - commission)
            capital += shares * proceeds
            trades.append({
                "Date": idx, "Type": "SELL", "Price": round(sell_price, 2),
                "Shares": shares, "Value": round(shares * sell_price, 2)
            })
            shares = 0
            position = False

        equity_curve.append({
            "Date": idx,
            "Portfolio_Value": round(capital + shares * close, 2),
            "Buy_Hold_Value": round(initial_capital * close / float(df.iloc[0]["Close"]), 2),
            "Score": score,
        })

    # Close any open position
    if position and len(df) > 0:
        last_close = float(df.iloc[-1]["Close"])
        capital += shares * last_close * (1 - commission - slippage)
        shares = 0

    # Calculate metrics
    equity_df = pd.DataFrame(equity_curve)
    if equity_df.empty:
        return {"error": "No equity data generated"}

    final_value = equity_df["Portfolio_Value"].iloc[-1]
    buy_hold_final = equity_df["Buy_Hold_Value"].iloc[-1]

    total_return = (final_value - initial_capital) / initial_capital * 100
    buy_hold_return = (buy_hold_final - initial_capital) / initial_capital * 100

    # Trade analysis
    trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
    win_trades = 0
    loss_trades = 0
    profits = []

    if not trades_df.empty:
        buys = trades_df[trades_df["Type"] == "BUY"]
        sells = trades_df[trades_df["Type"] == "SELL"]
        n_pairs = min(len(buys), len(sells))
        for i in range(n_pairs):
            pnl = sells.iloc[i]["Price"] - buys.iloc[i]["Price"]
            profits.append(pnl)
            if pnl > 0:
                win_trades += 1
            else:
                loss_trades += 1

    total_trades = win_trades + loss_trades
    win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0

    # Sharpe Ratio
    daily_returns = equity_df["Portfolio_Value"].pct_change().dropna()
    sharpe = 0
    if len(daily_returns) > 0 and daily_returns.std() > 0:
        sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)

    # Max Drawdown
    rolling_max = equity_df["Portfolio_Value"].cummax()
    drawdown = (equity_df["Portfolio_Value"] - rolling_max) / rolling_max * 100
    max_drawdown = drawdown.min()

    # Profit Factor
    gross_profit = sum(p for p in profits if p > 0) if profits else 0
    gross_loss = abs(sum(p for p in profits if p < 0)) if profits else 1
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

    return {
        "symbol": symbol,
        "initial_capital": initial_capital,
        "final_value": round(final_value, 2),
        "total_return_pct": round(total_return, 2),
        "buy_hold_return_pct": round(buy_hold_return, 2),
        "alpha": round(total_return - buy_hold_return, 2),
        "total_trades": total_trades,
        "win_trades": win_trades,
        "loss_trades": loss_trades,
        "win_rate_pct": round(win_rate, 2),
        "sharpe_ratio": round(sharpe, 2),
        "max_drawdown_pct": round(max_drawdown, 2),
        "profit_factor": round(profit_factor, 2),
        "trades": trades_df,
        "equity_curve": equity_df,
    }


def backtest_portfolio(symbols: list, timeframe: str = "long_term") -> pd.DataFrame:
    """
    Backtest multiple stocks and return a comparison table.
    """
    results = []
    for symbol in symbols:
        print(f"  Backtesting {symbol}...")
        res = backtest_stock(symbol, timeframe)
        if "error" not in res:
            results.append({
                "Symbol": res["symbol"],
                "Return%": res["total_return_pct"],
                "B&H Return%": res["buy_hold_return_pct"],
                "Alpha%": res["alpha"],
                "Win Rate%": res["win_rate_pct"],
                "Trades": res["total_trades"],
                "Sharpe": res["sharpe_ratio"],
                "Max DD%": res["max_drawdown_pct"],
                "Profit Factor": res["profit_factor"],
            })
    
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values("Return%", ascending=False).reset_index(drop=True)
    return df


if __name__ == "__main__":
    print("Backtesting RELIANCE...")
    result = backtest_stock("RELIANCE", "long_term")
    if "error" not in result:
        print(f"\n📊 Results:")
        print(f"  Return: {result['total_return_pct']}%")
        print(f"  Buy & Hold: {result['buy_hold_return_pct']}%")
        print(f"  Alpha: {result['alpha']}%")
        print(f"  Win Rate: {result['win_rate_pct']}%")
        print(f"  Sharpe: {result['sharpe_ratio']}")
        print(f"  Max Drawdown: {result['max_drawdown_pct']}%")
    else:
        print(result["error"])
