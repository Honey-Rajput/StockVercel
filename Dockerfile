# Python Backend Dockerfile
# For running the ML analysis pipeline on a schedule

FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY *.py ./
COPY stocks.xlsx ./

# Create output directories
RUN mkdir -p output/history models

# Default: run scheduler
CMD ["python", "scheduler.py"]
