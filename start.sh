#!/bin/bash
# Start the Telegram Bot in the background
python telegram_bot.py &

# Start the Scheduler in the background
python scheduler.py &

# Start the Streamlit Dashboard in the foreground
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
