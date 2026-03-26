"""
Streamlit Dashboard
Live UI for stock recommendations, backtesting, portfolio allocation, and history.
"""
import os
import sys
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))
import config

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="🤖 AI Stock Advisor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Root variables */
:root {
    --bg-primary: #0a0e17;
    --bg-secondary: #111827;
    --bg-card: #1a1f2e;
    --accent-blue: #3b82f6;
    --accent-green: #10b981;
    --accent-red: #ef4444;
    --accent-yellow: #f59e0b;
    --accent-purple: #8b5cf6;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --border-color: #1e293b;
    --glow-blue: rgba(59, 130, 246, 0.15);
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, var(--bg-primary) 0%, #0f172a 50%, #0a0e17 100%);
    color: var(--text-primary);
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827 0%, #0f172a 100%);
    border-right: 1px solid var(--border-color);
}

/* Title styling */
.main-title {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6, #ec4899);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.5rem;
    font-weight: 800;
    text-align: center;
    margin-bottom: 0;
    letter-spacing: -0.02em;
}

.sub-title {
    color: var(--text-secondary);
    text-align: center;
    font-size: 1rem;
    font-weight: 400;
    margin-top: 0;
}

/* Metric cards */
.metric-card {
    background: linear-gradient(135deg, var(--bg-card) 0%, rgba(30, 41, 59, 0.8) 100%);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    backdrop-filter: blur(10px);
    transition: transform 0.2s, box-shadow 0.2s;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(59, 130, 246, 0.1);
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.metric-label {
    color: var(--text-secondary);
    font-size: 0.85rem;
    margin-top: 4px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Signal badges */
.signal-strong-buy { 
    background: linear-gradient(135deg, #059669, #10b981); 
    color: white; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.8rem;
}
.signal-buy { 
    background: linear-gradient(135deg, #2563eb, #3b82f6); 
    color: white; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.8rem;
}
.signal-hold { 
    background: linear-gradient(135deg, #d97706, #f59e0b); 
    color: white; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.8rem;
}
.signal-sell { 
    background: linear-gradient(135deg, #dc2626, #ef4444); 
    color: white; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.8rem;
}

/* Score bar */
.score-bar-container {
    background: rgba(30, 41, 59, 0.5);
    border-radius: 10px;
    height: 8px;
    overflow: hidden;
}
.score-bar {
    height: 100%;
    border-radius: 10px;
    transition: width 0.5s ease;
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 8px 20px;
    font-weight: 500;
}

/* Cards */
.stock-card {
    background: linear-gradient(135deg, var(--bg-card), rgba(30, 41, 59, 0.6));
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 8px;
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================
@st.cache_data(ttl=300)
def load_latest_results():
    """Load the most recent recommendation results."""
    files = sorted(
        [f for f in os.listdir(config.OUTPUT_DIR) if f.startswith("recommendations_") and f.endswith(".xlsx")],
        reverse=True
    )
    if not files:
        return None, None

    latest = files[0]
    date_str = latest.replace("recommendations_", "").replace(".xlsx", "")
    filepath = os.path.join(config.OUTPUT_DIR, latest)

    try:
        xls = pd.ExcelFile(filepath)
        results = {}
        for sheet in xls.sheet_names:
            tf_key = sheet.lower().replace(" ", "_")
            results[tf_key] = pd.read_excel(xls, sheet_name=sheet, index_col=0)
        return results, date_str
    except Exception:
        return None, None


def load_history():
    """Load all history files."""
    from recommendation_engine import load_history as _load_history
    return _load_history()


def get_score_color(score):
    """Return color based on score value."""
    if score >= 80:
        return "#10b981"
    elif score >= 65:
        return "#3b82f6"
    elif score >= 50:
        return "#f59e0b"
    elif score >= 35:
        return "#f97316"
    else:
        return "#ef4444"


def render_metric_card(label, value, icon=""):
    """Render a styled metric card."""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{icon} {value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def render_stock_table(df, show_cols=None):
    """Render a styled stock table."""
    if df.empty:
        st.info("No data available. Run the analysis first!")
        return

    if show_cols:
        display_df = df[show_cols].copy()
    else:
        display_df = df.copy()

    st.dataframe(
        display_df,
        use_container_width=True,
        height=min(400, len(display_df) * 40 + 40),
    )


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown('<h2 style="text-align:center;">⚡ Control Panel</h2>', unsafe_allow_html=True)
    st.divider()

    # Run Analysis button
    if st.button("🚀 Run Analysis Now", use_container_width=True, type="primary"):
        with st.spinner("Running full analysis... This may take a few minutes."):
            try:
                from recommendation_engine import run_full_analysis, save_results
                results = run_full_analysis()
                save_results(results)
                st.success("✅ Analysis complete!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()

    # Status
    results, date_str = load_latest_results()
    if results:
        st.success(f"📅 Latest: {date_str}")
        total_stocks = sum(len(df) for df in results.values() if not df.empty)
        st.metric("Stocks Analyzed", total_stocks // max(len(results), 1))
    else:
        st.warning("No results yet. Click 'Run Analysis'")

    st.divider()
    st.markdown("""
    <div style="text-align:center; color: #64748b; font-size: 0.75rem;">
        🤖 AI Stock Advisor v1.0<br>
        Powered by ML + Technical + Fundamental Analysis
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# MAIN HEADER
# ============================================================
st.markdown('<h1 class="main-title">🤖 AI Stock Advisor</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">ML-Powered Stock Recommendations for Indian Markets</p>', unsafe_allow_html=True)
st.markdown("")

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Today's Picks", "📈 Stock Deep Dive", "📉 Backtesting",
    "💰 Portfolio", "📜 Week History", "⚙️ Settings"
])

# ============================================================
# TAB 1: TODAY'S PICKS
# ============================================================
with tab1:
    results, date_str = load_latest_results()

    if not results:
        st.markdown("""
        <div style="text-align:center; padding: 60px 20px;">
            <h2>📊 No recommendations yet</h2>
            <p style="color: var(--text-secondary);">Click <b>🚀 Run Analysis Now</b> in the sidebar to get started!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Quick metrics
        col1, col2, col3, col4 = st.columns(4)
        all_stocks = pd.concat([df for df in results.values() if not df.empty], ignore_index=True)

        with col1:
            buy_count = len(all_stocks[all_stocks["Signal"].str.contains("Buy", na=False)])
            render_metric_card("Buy Signals", buy_count, "🟢")
        with col2:
            sell_count = len(all_stocks[all_stocks["Signal"].str.contains("Sell", na=False)])
            render_metric_card("Sell Signals", sell_count, "🔴")
        with col3:
            avg_score = round(all_stocks["Composite_Score"].mean(), 1) if not all_stocks.empty else 0
            render_metric_card("Avg Score", avg_score, "📊")
        with col4:
            render_metric_card("Last Updated", date_str or "N/A", "📅")

        st.markdown("")

        # Timeframe tabs within picks
        for tf_key, tf_label in [("intraday", "⚡ Intraday"), ("short_term", "📅 Short Term (1-5 Days)"), ("long_term", "🗓️ Long Term (1-3 Months)")]:
            df = results.get(tf_key, pd.DataFrame())
            if df.empty:
                continue

            st.markdown(f"### {tf_label}")

            # Top 10
            top10 = df.head(10)

            # Score visualization
            fig = go.Figure()
            colors = [get_score_color(s) for s in top10["Composite_Score"]]

            fig.add_trace(go.Bar(
                x=top10["Composite_Score"],
                y=top10["Symbol"],
                orientation="h",
                marker=dict(color=colors, line=dict(width=0)),
                text=[f"{s:.0f}" for s in top10["Composite_Score"]],
                textposition="outside",
                textfont=dict(color="#f1f5f9", size=12),
            ))
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=350,
                margin=dict(l=0, r=60, t=10, b=10),
                xaxis=dict(range=[0, 110], showgrid=False, zeroline=False, visible=False),
                yaxis=dict(autorange="reversed", tickfont=dict(size=13, color="#f1f5f9")),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Detailed table
            show_cols = ["Symbol", "Name", "Close", "Change%", "Composite_Score", "Signal",
                         "Entry", "Stop_Loss", "Target_1", "Target_2"]
            available_cols = [c for c in show_cols if c in df.columns]
            render_stock_table(top10, available_cols)
            st.markdown("---")


# ============================================================
# TAB 2: STOCK DEEP DIVE
# ============================================================
with tab2:
    st.markdown("### 📈 Stock Deep Dive")

    results, _ = load_latest_results()
    if results:
        all_symbols = set()
        for df in results.values():
            if not df.empty:
                all_symbols.update(df["Symbol"].tolist())
        all_symbols = sorted(all_symbols)
    else:
        try:
            from data_fetcher import load_stock_universe
            stocks_df = load_stock_universe()
            all_symbols = stocks_df["Symbol"].tolist()
        except Exception:
            all_symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]

    selected = st.selectbox("Select Stock", all_symbols, index=0)

    if selected:
        with st.spinner(f"Loading {selected} data..."):
            try:
                from data_fetcher import fetch_ohlcv, fetch_fundamentals
                from technical_indicators import calculate_all_indicators, generate_technical_score, generate_fundamental_score

                ohlcv = fetch_ohlcv(selected, "long_term")
                if not ohlcv.empty:
                    df = calculate_all_indicators(ohlcv)
                    fund = fetch_fundamentals(selected)

                    # Scores
                    tech_score = generate_technical_score(df)
                    fund_score = generate_fundamental_score(fund)

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        render_metric_card("Technical Score", f"{tech_score:.0f}", "📊")
                    with col2:
                        render_metric_card("Fundamental Score", f"{fund_score:.0f}", "💎")
                    with col3:
                        combined = round((tech_score + fund_score) / 2, 1)
                        render_metric_card("Combined", f"{combined:.0f}", "🎯")

                    st.markdown("")

                    # Candlestick chart
                    fig = make_subplots(
                        rows=3, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03,
                        row_heights=[0.6, 0.2, 0.2],
                        subplot_titles=("Price", "RSI", "MACD"),
                    )

                    # Candlestick
                    fig.add_trace(go.Candlestick(
                        x=df.index, open=df["Open"], high=df["High"],
                        low=df["Low"], close=df["Close"], name="Price",
                        increasing_line_color="#10b981",
                        decreasing_line_color="#ef4444",
                    ), row=1, col=1)

                    # Moving averages
                    if "SMA_20" in df.columns:
                        fig.add_trace(go.Scatter(x=df.index, y=df["SMA_20"], name="SMA 20",
                                                 line=dict(color="#3b82f6", width=1)), row=1, col=1)
                    if "SMA_50" in df.columns:
                        fig.add_trace(go.Scatter(x=df.index, y=df["SMA_50"], name="SMA 50",
                                                 line=dict(color="#f59e0b", width=1)), row=1, col=1)
                    if "BB_Upper" in df.columns:
                        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Upper"], name="BB Upper",
                                                 line=dict(color="#8b5cf6", width=1, dash="dot")), row=1, col=1)
                        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Lower"], name="BB Lower",
                                                 line=dict(color="#8b5cf6", width=1, dash="dot")), row=1, col=1)

                    # RSI
                    if "RSI" in df.columns:
                        fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI",
                                                 line=dict(color="#8b5cf6", width=1.5)), row=2, col=1)
                        fig.add_hline(y=70, line_dash="dot", line_color="#ef4444", row=2, col=1)
                        fig.add_hline(y=30, line_dash="dot", line_color="#10b981", row=2, col=1)

                    # MACD
                    if "MACD" in df.columns:
                        fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD",
                                                 line=dict(color="#3b82f6", width=1.5)), row=3, col=1)
                        fig.add_trace(go.Scatter(x=df.index, y=df["MACD_Signal"], name="Signal",
                                                 line=dict(color="#f59e0b", width=1.5)), row=3, col=1)
                        colors = ["#10b981" if v >= 0 else "#ef4444" for v in df["MACD_Hist"].fillna(0)]
                        fig.add_trace(go.Bar(x=df.index, y=df["MACD_Hist"], name="Histogram",
                                             marker_color=colors), row=3, col=1)

                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        height=700,
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        xaxis_rangeslider_visible=False,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Fundamentals
                    st.markdown("### 💎 Fundamentals")
                    fund_cols = st.columns(4)
                    fund_items = [
                        ("P/E", fund.get("PE")), ("P/B", fund.get("PB")),
                        ("ROE", f"{fund['ROE']:.1%}" if fund.get("ROE") else "N/A"),
                        ("D/E", fund.get("DebtEquity")),
                        ("EPS", fund.get("EPS")), ("Beta", fund.get("Beta")),
                        ("Div Yield", f"{fund['DividendYield']:.2%}" if fund.get("DividendYield") else "N/A"),
                        ("Profit Margin", f"{fund['ProfitMargin']:.1%}" if fund.get("ProfitMargin") else "N/A"),
                    ]
                    for i, (label, val) in enumerate(fund_items):
                        with fund_cols[i % 4]:
                            st.metric(label, val if val else "N/A")
                else:
                    st.error(f"No data available for {selected}")
            except Exception as e:
                st.error(f"Error loading data: {e}")


# ============================================================
# TAB 3: BACKTESTING
# ============================================================
with tab3:
    st.markdown("### 📉 Backtest Simulator")

    col1, col2, col3 = st.columns(3)
    with col1:
        bt_symbol = st.text_input("Stock Symbol", "RELIANCE")
    with col2:
        bt_capital = st.number_input("Initial Capital (₹)", value=100000, step=10000)
    with col3:
        bt_timeframe = st.selectbox("Timeframe", ["long_term", "short_term"], index=0)

    col4, col5 = st.columns(2)
    with col4:
        buy_thresh = st.slider("Buy Threshold (Score)", 50, 90, 65)
    with col5:
        sell_thresh = st.slider("Sell Threshold (Score)", 20, 60, 45)

    if st.button("🔬 Run Backtest", type="primary", use_container_width=True):
        with st.spinner(f"Backtesting {bt_symbol}..."):
            try:
                from backtester import backtest_stock

                result = backtest_stock(
                    bt_symbol, bt_timeframe, bt_capital,
                    buy_threshold=buy_thresh, sell_threshold=sell_thresh
                )

                if "error" in result:
                    st.error(result["error"])
                else:
                    # Metrics
                    m1, m2, m3, m4 = st.columns(4)
                    with m1:
                        color = "normal" if result["total_return_pct"] >= 0 else "inverse"
                        st.metric("Strategy Return", f"{result['total_return_pct']}%",
                                  f"vs B&H: {result['buy_hold_return_pct']}%")
                    with m2:
                        st.metric("Win Rate", f"{result['win_rate_pct']}%",
                                  f"{result['total_trades']} trades")
                    with m3:
                        st.metric("Sharpe Ratio", result["sharpe_ratio"])
                    with m4:
                        st.metric("Max Drawdown", f"{result['max_drawdown_pct']}%")

                    m5, m6 = st.columns(2)
                    with m5:
                        st.metric("Profit Factor", result["profit_factor"])
                    with m6:
                        alpha_delta = "normal" if result["alpha"] >= 0 else "inverse"
                        st.metric("Alpha", f"{result['alpha']}%")

                    # Equity curve
                    eq = result["equity_curve"]
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=eq["Date"], y=eq["Portfolio_Value"],
                        name="Strategy", line=dict(color="#3b82f6", width=2),
                        fill="tozeroy", fillcolor="rgba(59, 130, 246, 0.1)",
                    ))
                    fig.add_trace(go.Scatter(
                        x=eq["Date"], y=eq["Buy_Hold_Value"],
                        name="Buy & Hold", line=dict(color="#94a3b8", width=1.5, dash="dot"),
                    ))
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        height=400,
                        title="Equity Curve",
                        yaxis_title="Portfolio Value (₹)",
                        showlegend=True,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Trade log
                    if not result["trades"].empty:
                        st.markdown("### 📋 Trade Log")
                        st.dataframe(result["trades"], use_container_width=True)
            except Exception as e:
                st.error(f"Backtest error: {e}")


# ============================================================
# TAB 4: AI PREDICTOR
# ============================================================
with tab4:
    st.markdown("### 🔮 AI Stock Predictor")
    
    col_sym, col_tf = st.columns([2, 1])
    with col_sym:
        pred_symbol = st.text_input("Enter Stock Symbol", "RELIANCE", key="st_pred_sym").upper()
    with col_tf:
        pred_timeframe = st.selectbox("Timeframe", 
                                      ["5 min", "15 min", "1 hour", "4 hours", "1 day", "1 week", "1 month"],
                                      index=4, key="st_pred_tf")

    if st.button("✨ Generate AI Prediction", type="primary", use_container_width=True):
        if not pred_symbol:
            st.warning("Please enter a symbol.")
        else:
            with st.spinner(f"AI is analyzing {pred_symbol}..."):
                try:
                    from telegram_bot import get_ai_prediction
                    # get_ai_prediction is async, so we need to run it in a loop
                    import asyncio
                    
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    response = loop.run_until_complete(get_ai_prediction(pred_symbol, pred_timeframe))
                    
                    st.markdown("---")
                    st.markdown(response)
                    st.markdown("---")
                    st.info("💡 Note: This analysis is powered by Gemini 2.5 Flash using real-time database metrics.")
                except Exception as e:
                    st.error(f"Error generating prediction: {e}")


# ============================================================
# TAB 5: WEEK HISTORY
# ============================================================
with tab5:
    st.markdown("### 📜 Past 5 Trading Days")

    history = load_history()

    if not history:
        st.info("No historical data yet. Results will be saved automatically after each analysis run.")
    else:
        dates = sorted(history.keys(), reverse=True)
        st.markdown(f"**Available dates:** {', '.join(dates)}")

        selected_tf = st.selectbox("Timeframe", ["long_term", "short_term", "intraday"],
                                    index=0, key="hist_tf")

        # Comparison view
        comparison_data = []
        for date in dates:
            day_data = history[date]
            df = day_data.get(selected_tf, pd.DataFrame())
            if df.empty:
                continue

            for _, row in df.head(10).iterrows():
                comparison_data.append({
                    "Date": date,
                    "Symbol": row.get("Symbol", ""),
                    "Score": row.get("Composite_Score", 0),
                    "Signal": row.get("Signal", ""),
                    "Close": row.get("Close", 0),
                })

        if comparison_data:
            comp_df = pd.DataFrame(comparison_data)

            # Heatmap: symbols across dates
            pivot = comp_df.pivot_table(index="Symbol", columns="Date", values="Score", aggfunc="first")
            pivot = pivot.fillna(0)

            fig = go.Figure(data=go.Heatmap(
                z=pivot.values,
                x=pivot.columns.tolist(),
                y=pivot.index.tolist(),
                colorscale=[
                    [0.0, "#ef4444"], [0.35, "#f59e0b"],
                    [0.5, "#fbbf24"], [0.65, "#3b82f6"],
                    [1.0, "#10b981"],
                ],
                text=[[f"{v:.0f}" for v in row] for row in pivot.values],
                texttemplate="%{text}",
                textfont=dict(size=11, color="white"),
                zmin=0, zmax=100,
                colorbar=dict(title="Score"),
            ))
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=max(300, len(pivot) * 30 + 100),
                title=f"Score Heatmap — {selected_tf.replace('_',' ').title()}",
                xaxis_title="Date",
                yaxis_title="Stock",
            )
            st.plotly_chart(fig, use_container_width=True)

            # Day-by-day table selector
            selected_date = st.selectbox("View Details For", dates)
            day_df = history.get(selected_date, {}).get(selected_tf, pd.DataFrame())
            if not day_df.empty:
                show_cols = [c for c in ["Symbol", "Name", "Close", "Composite_Score", "Signal",
                                          "Target_1", "Target_2", "Stop_Loss"] if c in day_df.columns]
                st.dataframe(day_df[show_cols].head(15), use_container_width=True)
        else:
            st.info("No data for this timeframe in history.")


# ============================================================
# TAB 6: SETTINGS
# ============================================================
with tab6:
    st.markdown("### ⚙️ Configuration")

    with st.expander("📡 Alert Settings", expanded=True):
        alert_mode = st.selectbox("Alert Mode",
                                   ["telegram", "whatsapp_twilio", "whatsapp_pywhatkit", "all", "none"],
                                   index=0)
        tg_token = st.text_input("Telegram Bot Token", value=config.TELEGRAM_BOT_TOKEN,
                                  type="password")
        tg_chat = st.text_input("Telegram Chat ID", value=config.TELEGRAM_CHAT_ID)

        if st.button("💾 Save Alert Settings"):
            st.success("Settings saved for this session. Update config.py for permanent changes.")

    with st.expander("📅 Scheduler"):
        st.markdown("**Scheduled Times (IST, Mon-Fri):**")
        for name, time_str in config.SCHEDULE_TIMES.items():
            st.text(f"  {name}: {time_str}")

        st.info("To start the scheduler, run: `python scheduler.py`")

    with st.expander("🎛️ ML Parameters"):
        st.json({
            "RF": config.RF_PARAMS,
            "XGBoost": config.XGB_PARAMS,
            "Ensemble Weights": config.ENSEMBLE_WEIGHTS,
            "Scoring Weights": config.SCORING_WEIGHTS,
        })

    with st.expander("📊 Signal Thresholds"):
        st.json(config.SIGNAL_THRESHOLDS)

    with st.expander("💰 Risk Profiles"):
        st.json(config.RISK_PROFILES)
