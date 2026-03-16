FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_NAME="AtlasCore API" \
    PORT=8000 \
    SQLITE_PATH=/app/data/atlascore.db \
    CSV_EXPORT_DIR=/app/data/exports \
    DOCUMENT_LOCAL_STORAGE_DIR=/app/data/uploads \
    GRAPH_ENABLED=true \
    GRAPH_RELOAD_ON_START=true \
    GRAPH_EXPORT_DIR=/app/data/graph_exports \
    GRAPH_IMPORT_DIR=/app/data/graph_imports \
    GRAPH_INSTANCE_LOCAL_PATH=/app/data/atlascore_graph.db \
    GRAPH_INSTANCE_ID=atlascore-instance-local

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY config ./config

RUN mkdir -p /app/data/exports /app/data/uploads /app/data/graph_exports /app/data/graph_imports

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
