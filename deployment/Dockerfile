FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN addgroup --system appgroup && adduser --system --group appuser
USER appuser

# Use $PORT so Render can assign whatever port it wants
EXPOSE 8000

# For FastAPI backend:
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}

# If this is the Streamlit frontend instead, use:
# CMD streamlit run frontend/streamlit_app.py --server.port ${PORT:-8000} --server.address 0.0.0.0
