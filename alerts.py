"""
Alerts Module
Send stock recommendations via Telegram and WhatsApp.
"""
import asyncio
from datetime import datetime

import config


def _format_alert_message(results: dict, top_n: int = 5) -> str:
    """Format recommendation results into a clean message."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"🤖 Stock Recommendations — {now}\n"]

    for tf, df in results.items():
        if df.empty:
            continue

        tf_label = tf.replace("_", " ").title()
        lines.append(f"\n📊 {tf_label} (Top {top_n})")
        lines.append("─" * 30)

        for _, row in df.head(top_n).iterrows():
            lines.append(
                f"{row['Signal']} {row['Symbol']}\n"
                f"   💰 ₹{row['Close']}  |  Score: {row['Composite_Score']}\n"
                f"   🎯 T1: ₹{row['Target_1']}  T2: ₹{row['Target_2']}\n"
                f"   🛑 SL: ₹{row['Stop_Loss']}"
            )
        lines.append("")

    lines.append("⚠️ Not financial advice. Do your own research.")
    return "\n".join(lines)


# ============================================================
# TELEGRAM
# ============================================================
async def _send_telegram_async(message: str):
    """Send message via Telegram bot."""
    try:
        from telegram import Bot
        bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        
        # Split long messages (Telegram limit: 4096 chars)
        chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
        for chunk in chunks:
            await bot.send_message(
                chat_id=config.TELEGRAM_CHAT_ID,
                text=chunk,
                parse_mode=None,
            )
        print("  ✓ Telegram alert sent")
    except Exception as e:
        print(f"  ✗ Telegram error: {e}")


def send_telegram(message: str):
    """Synchronous wrapper for Telegram."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_send_telegram_async(message))
        else:
            asyncio.run(_send_telegram_async(message))
    except RuntimeError:
        asyncio.run(_send_telegram_async(message))


# ============================================================
# WHATSAPP (Twilio)
# ============================================================
def send_whatsapp_twilio(message: str):
    """Send message via Twilio WhatsApp API."""
    if not config.TWILIO_ACCOUNT_SID or not config.TWILIO_AUTH_TOKEN:
        print("  ⚠ Twilio not configured, skipping WhatsApp")
        return

    try:
        from twilio.rest import Client
        client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
        
        msg = client.messages.create(
            body=message[:1600],  # WhatsApp limit
            from_=config.TWILIO_WHATSAPP_FROM,
            to=config.TWILIO_WHATSAPP_TO,
        )
        print(f"  ✓ WhatsApp (Twilio) sent: {msg.sid}")
    except Exception as e:
        print(f"  ✗ WhatsApp (Twilio) error: {e}")


# ============================================================
# WHATSAPP (pywhatkit fallback)
# ============================================================
def send_whatsapp_pywhatkit(message: str):
    """Send message via pywhatkit (opens WhatsApp Web)."""
    try:
        import pywhatkit
        now = datetime.now()
        hour = now.hour
        minute = now.minute + 2  # Send 2 minutes from now

        if minute >= 60:
            hour += 1
            minute -= 60

        pywhatkit.sendwhatmsg(
            config.PYWHATKIT_PHONE,
            message[:1000],
            hour, minute,
            wait_time=15,
            tab_close=True,
        )
        print("  ✓ WhatsApp (pywhatkit) sent")
    except Exception as e:
        print(f"  ✗ WhatsApp (pywhatkit) error: {e}")


# ============================================================
# MAIN ALERT DISPATCHER
# ============================================================
def send_alerts(results: dict, top_n: int = 5):
    """
    Send alerts based on configured ALERT_MODE.
    
    Args:
        results: {"intraday": df, "short_term": df, "long_term": df}
        top_n: Number of top stocks to include
    """
    message = _format_alert_message(results, top_n)
    mode = config.ALERT_MODE.lower()

    print(f"\n📲 Sending alerts (mode: {mode})...")

    if mode in ("telegram", "all"):
        send_telegram(message)

    if mode in ("whatsapp_twilio", "all"):
        send_whatsapp_twilio(message)

    if mode in ("whatsapp_pywhatkit", "all"):
        send_whatsapp_pywhatkit(message)


if __name__ == "__main__":
    # Test with dummy data
    import pandas as pd

    dummy_results = {
        "short_term": pd.DataFrame([{
            "Symbol": "RELIANCE", "Signal": "🟢 Strong Buy",
            "Close": 2500, "Composite_Score": 85,
            "Target_1": 2650, "Target_2": 2800, "Stop_Loss": 2400,
        }])
    }

    msg = _format_alert_message(dummy_results)
    print(msg)
    print("\n(Actual sending skipped in test mode)")
