# Python Backend Dockerfile
# For running the Dashboard, Bot, and Scheduler

FROM python:3.10-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and config
COPY . .

# Ensure start script is executable
RUN chmod +x start.sh

# Create output directories
RUN mkdir -p output/history models

# Default to the all-in-one start script
CMD ["./start.sh"]
