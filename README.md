# AtlasCore API

AtlasCore API is a Docker-first FastAPI backend scaffold for Azure App Service (custom container).

This project focuses on:
- Auth boundary (JWT + local users + RBAC)
- Admin document metadata management
- Graph query API façade for Neo4j
- Integration adapter layer (Dify placeholder)

It does **not** implement RAG main pipeline or chat answer generation.

## 1. Quick Start (Local)

### Prerequisites
- Python 3.11+
- `pip`
- Optional: Docker

### Setup

```bash
cd /home/Project/AtlasCore
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
```

### Health Check

```bash
curl -s http://127.0.0.1:${PORT:-8000}/health
```

Expected response:

```json
{"status":"ok","service":"AtlasCore API"}
```

## 2. Environment Variables

All critical configs are loaded from environment variables via `app/core/config.py`.

| Variable | Required Now | Required in Production | Description |
|---|---|---|---|
| `APP_NAME` | No | No | Service display name |
| `APP_ENV` | No | Yes (set explicitly) | `development/staging/production/test` |
| `PORT` | No | Yes | HTTP listen port (Azure compatible) |
| `LOG_LEVEL` | No | Yes | `DEBUG/INFO/WARNING/ERROR/CRITICAL` |
| `JWT_SECRET` | No (dev/test fallback) | Yes | JWT signing secret |
| `DATABASE_URL` | No | Yes (when auth/admin DB features enabled) | PostgreSQL DSN |
| `NEO4J_URI` | No | Yes (when graph features enabled) | AuraDB URI |
| `NEO4J_DATABASE` | No | No | Neo4j database name (default `neo4j`) |
| `NEO4J_USERNAME` | No | Yes (with graph enabled) | Neo4j user |
| `NEO4J_PASSWORD` | No | Yes (with graph enabled) | Neo4j password |
| `DIFY_BASE_URL` | No | Yes (when Dify integration enabled) | Dify API endpoint |
| `DIFY_API_KEY` | No | Yes (when Dify integration enabled) | Dify API key |
| `DOCUMENT_LOCAL_STORAGE_DIR` | No | No | Local upload placeholder directory |

Notes:
- Service can start without PostgreSQL / Neo4j / Dify credentials.
- `/health` is intentionally independent from DB and Neo4j availability.

## 3. Tests and Local Validation

Run all tests:

```bash
pytest -q
```

Current baseline includes:
- Health endpoint behavior
- Config loading and validation
- JWT/password utilities
- RBAC and service-level behavior
- Graph service and mapper behavior (unit-level)
- Dify placeholder adapter behavior

## 4. Docker Usage

### Build Image

```bash
docker build -t atlascore-api:local .
```

### Run Container

```bash
docker run --rm -p 8000:8000 -e PORT=8000 --name atlascore-api atlascore-api:local
```

### Verify in Container

```bash
curl -s http://127.0.0.1:8000/health
```

Expected:

```json
{"status":"ok","service":"AtlasCore API"}
```

## 5. Current Scope (Done vs Placeholder)

### Implemented
- FastAPI app skeleton with layered structure (`api/core/db/models/services/repositories`)
- Health endpoint
- JWT + local user auth skeleton
- RBAC (`user` / `admin`) dependency pattern
- PostgreSQL model/session/Alembic scaffolding
- Admin document metadata module skeleton
- Graph API skeleton for Neo4j queries
- Dify integration adapter placeholder layer
- Dockerfile + docker runtime path
- Unit test baseline

### Placeholder / Not Fully Integrated Yet
- Real Dify API calls (currently staged placeholder responses)
- End-to-end PostgreSQL CRUD for all business flows
- Real Neo4j connection validation in integration tests
- GraphRAG orchestration logic
- Azure Key Vault + Managed Identity runtime integration
- CI/CD pipeline automation

## 6. Manual Azure Deployment Bridge (No CI/CD)

This section describes the manual path: `Docker -> ACR -> App Service`.

### Step A: Build and Tag Image

```bash
docker build -t atlascore-api:local .
docker tag atlascore-api:local <acr-name>.azurecr.io/atlascore-api:<tag>
```

### Step B: Push to ACR

```bash
az acr login --name <acr-name>
docker push <acr-name>.azurecr.io/atlascore-api:<tag>
```

### Step C: Configure App Service (Custom Container)
- Set container image to: `<acr-name>.azurecr.io/atlascore-api:<tag>`
- Configure app settings (environment variables):
  - `PORT=8000`
  - `APP_ENV=production`
  - `JWT_SECRET=<secure-value>`
  - Optional stage-based configs: `DATABASE_URL`, `NEO4J_*`, `DIFY_*`

### Step D: Verify Runtime
- Open App Service URL `/health`
- Confirm HTTP 200 with `{"status":"ok","service":"AtlasCore API"}`
- Check container logs if startup fails

## 7. Next Azure Integrations (Suggested Order)

1. Connect PostgreSQL Flexible Server
- Set `DATABASE_URL` in App Service settings
- Run `alembic upgrade head` against target DB
- Validate auth/admin DB flows

2. Connect Neo4j AuraDB
- Set `NEO4J_URI`, `NEO4J_DATABASE`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`
- Validate `/graph/*` endpoints

3. Enable Dify Real Calls
- Set `DIFY_BASE_URL`, `DIFY_API_KEY`
- Replace placeholder internals in `app/integrations/dify/client.py`

4. Move secrets to Azure Key Vault + Managed Identity
- Keep app code unchanged at service layer
- Swap secret injection strategy (App Settings references / runtime retrieval)

## 8. Architecture Guardrails

- Do not couple `/health` to DB or Neo4j connectivity.
- Keep external integration calls inside `app/integrations/*` only.
- Keep auth/authorization decisions in API backend (AtlasCore), not frontend.
- Keep Dify as integration target, not as AtlasCore core business logic owner.
