FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Render assigns a dynamic port via $PORT env var
EXPOSE 8000

# Single CMD only - use $PORT so Render can assign any port
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
