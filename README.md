# AtlasCore API

AtlasCore API is a FastAPI backend skeleton designed for Docker-first and Azure App Service deployment.

## Prerequisites

- Python 3.11+

## Local Run

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create local env file:

```bash
cp .env.example .env
```

4. Start server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
```

## Health Check

```bash
curl -s http://127.0.0.1:${PORT:-8000}/health
```

Expected response:

```json
{"status":"ok","service":"AtlasCore API"}
```

## Docker

Build image:

```bash
docker build -t atlascore-api:local .
```

Run container:

```bash
docker run --rm -p 8000:8000 -e PORT=8000 --name atlascore-api atlascore-api:local
```

Verify:

```bash
curl -s http://127.0.0.1:8000/health
```
