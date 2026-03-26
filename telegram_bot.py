import os
import asyncio
import logging
import json
import pandas as pd
import requests
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

import config
from alerts import _format_alert_message

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# ============================================================
# DB HELPERS
# ============================================================
def get_latest_signals(timeframe):
    """Fetch top 5 signals from Neon DB for a specific timeframe."""
    import psycopg2
    try:
        conn = psycopg2.connect(config.NEON_DB_URL)
        query = f"""
            SELECT symbol, signal, close, composite_score, target_1, target_2, stop_loss
            FROM recommendations
            WHERE timeframe = %s
            AND date = (SELECT MAX(date) FROM recommendations WHERE timeframe = %s)
            ORDER BY composite_score DESC
            LIMIT 5
        """
        df = pd.read_sql(query, conn, params=(timeframe, timeframe))
        conn.close()
        
        # Mapping to match alerts.py exactly
        column_map = {
            "symbol": "Symbol",
            "signal": "Signal",
            "close": "Close",
            "composite_score": "Composite_Score",
            "target_1": "Target_1",
            "target_2": "Target_2",
            "stop_loss": "Stop_Loss"
        }
        df.rename(columns=column_map, inplace=True)
        return df
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return pd.DataFrame()

# ============================================================
# AI PREDICTOR HELPER (Python version of the Next.js logic)
# ============================================================
async def get_ai_prediction(symbol, timeframe="1 day"):
    """Call Gemini for a stock prediction."""
    import psycopg2
    try:
        conn = psycopg2.connect(config.NEON_DB_URL)
        curr = conn.cursor()
        curr.execute("""
            SELECT close, rsi, macd_hist, target_1, target_2, stop_loss
            FROM recommendations
            WHERE symbol = %s
            AND date = (SELECT MAX(date) FROM recommendations)
            ORDER BY date DESC
            LIMIT 1
        """, (symbol.upper(),))
        row = curr.fetchone()
        conn.close()

        stats_context = ""
        if row:
            stats_context = f"""
            Latest Snapshot for {symbol}:
            - Price: INR {row[0]}
            - RSI: {row[1]}
            - MACD: {row[2]}
            - Targets: INR {row[3]}, INR {row[4]}
            """
        
        prompt = f"""
        Analyze {symbol} for {timeframe}.
        Current Market Context: {stats_context}
        
        Provide:
        1. Directional Sentiment (Bullish/Bearish/Neutral)
        2. Technical Levels (Pivot, S1-S3, R1-R3)
        3. Detailed Technical Justification.
        
        Keep it professional and concise for reading in Telegram. Give clear headings.
        """

        api_key = os.getenv("EURI_API_KEY")
        response = requests.post(
            "https://api.euron.one/api/v1/euri/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "gemini-2.5-flash",
                "messages": [
                    {"role": "system", "content": "You are a senior professional stock analyst."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            },
            timeout=30
        )
        data = response.json()
        if 'choices' not in data:
            logger.error(f"AI Response unexpected: {data}")
            return "⚠️ AI service returned an error. Please try again later."
        return data['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"AI Prediction Error: {e}")
        return f"Error generating prediction: {e}"

# ============================================================
# BOT HANDLERS
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message with options for on-demand reports."""
    keyboard = [
        [InlineKeyboardButton("📊 Intraday Top 5", callback_data='intraday')],
        [InlineKeyboardButton("📈 Short Term Top 5", callback_data='short_term')],
        [InlineKeyboardButton("🏦 Long Term Top 5", callback_data='long_term')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to AI Stock Advisor! 🤖\n\nCommands:\n/start - Show this menu\n/predict <SYMBOL> - Get AI analysis\n\nSelect an option below for latest signals:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks."""
    query = update.callback_query
    await query.answer()
    
    label = query.data.replace('_', ' ').title()
    await query.edit_message_text(text=f"🔄 Fetching latest {label} signals...")
    
    df = get_latest_signals(query.data)
    if df.empty:
        await query.edit_message_text(text=f"❌ No {label} signals found in the database. Please run an analysis first!")
        return

    message = _format_alert_message({query.data: df})
    await query.message.reply_text(message)

async def predict_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /predict <SYMBOL> [TIMEFRAME] command."""
    if not context.args:
        await update.message.reply_text("💡 Usage: `/predict RELIANCE` or `/predict TCS 15m`", parse_mode='Markdown')
        return
    
    symbol = context.args[0].upper()
    timeframe = context.args[1] if len(context.args) > 1 else "1 day"
    
    await update.message.reply_text(f"🔮 AI is analyzing {symbol} for {timeframe}... Please wait.")
    
    prediction = await get_ai_prediction(symbol, timeframe)
    await update.message.reply_text(prediction)

# ============================================================
# MAIN
# ============================================================
def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found!")
        return

    application = ApplicationBuilder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("predict", predict_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Add a handler for greetings (Hi, Hello, Hny)
    application.add_handler(MessageHandler(filters.Text(["Hi", "Hello", "Hny", "hi", "hello", "hny"]), start))
    
    print("Telegram Bot is running... (Press Ctrl+C to stop in terminal)")
    application.run_polling()

if __name__ == '__main__':
    main()
