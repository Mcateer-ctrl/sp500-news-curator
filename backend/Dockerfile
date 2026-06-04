FROM python:3.11-slim

WORKDIR /app

# System deps for torch + transformers
RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download FinBERT weights at build time so first startup is instant
# This bakes the model into the image layer — cached across rebuilds
RUN python -c "from transformers import pipeline; \
    pipeline('text-classification', model='ProsusAI/finbert', \
    cache_dir='/app/model_cache')"

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
