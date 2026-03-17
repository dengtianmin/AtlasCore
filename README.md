# AtlasCore

AtlasCore 是一个 SQLite-first 的 FastAPI 后端，已完成“第12步：联调前端、Dify、Azure 后端、SQLite、轻量图模块与多实例本地图库机制”。

## 第12步完成内容

- 前端统一调用 AtlasCore API。
- AtlasCore 内部调用 Dify 完成聊天主链路，前端不直接调用 Dify。
- 聊天接口同时支持阻塞式返回和 SSE 流式返回，前端聊天页默认使用流式输出。
- AtlasCore 将问答日志、反馈、文档元数据、导出记录写入业务 SQLite。
- AtlasCore 通过 SQLite + Python 轻量图模块提供图谱接口。
- AtlasCore 提供管理员 CSV 导出、图 SQLite 导入导出、图重载、文档同步与系统状态接口。
- 多实例运行时，每个实例只使用自己的本地 `GRAPH_INSTANCE_LOCAL_PATH`，不共享同一个 SQLite 图文件。

## 联调边界

- Dify 负责基础 RAG 问答主链路和最终答案生成。
- AtlasCore 负责系统 API、聊天封装、日志、反馈、导出、文档管理、图谱接口、管理员能力。
- 前端不直接访问 Dify。
- 前端不直接访问底层图存储。
- Neo4j / PostgreSQL 不是当前步骤的主依赖，`NEO4J_*` 仅保留为未来预留项。

## 权限模型

- 普通用户：无需登录，可访问 `/chat` 和 `/graph` 相关公开接口。
- 管理员：需要认证，可访问后台、文档管理、CSV 导出、图 SQLite 导入导出、图重载、联调状态接口。

## 前端页面入口

- `/`：默认跳转到 `/chat`。
- `/chat`：聊天页面。
- `/graph`：图谱页面。
- `/admin/login`：管理员登录入口。
- `/admin`：管理员后台首页。

## 关键接口

- `GET /health`
- `GET /health/ready`
- `POST /chat/messages`
- `POST /chat/messages/stream`
- `POST /chat/messages/{message_id}/feedback`
- `GET /graph/summary`
- `GET /graph/overview`
- `GET /graph/nodes/{node_id}`
- `GET /graph/nodes/{node_id}/neighbors`
- `GET /graph/subgraph/{node_id}`
- `GET /api/admin/logs`
- `GET /api/admin/logs/feedback`
- `POST /api/admin/exports/qa-logs`
- `POST /api/admin/exports/feedback`
- `GET /api/admin/exports/download/{filename}`
- `GET /api/admin/graph/status`
- `POST /api/admin/graph/export`
- `POST /api/admin/graph/import`
- `POST /api/admin/graph/reload`
- `GET /api/admin/system/status`
- `GET /admin/documents`
- `POST /admin/documents/upload`
- `DELETE /admin/documents/{document_id}`
- `POST /admin/documents/{document_id}/graph-sync`
- `POST /admin/documents/{document_id}/dify-sync`

## 关键环境变量

- `SQLITE_PATH`
- `CSV_EXPORT_DIR`
- `DOCUMENT_LOCAL_STORAGE_DIR`
- `GRAPH_ENABLED`
- `GRAPH_INSTANCE_LOCAL_PATH`
- `GRAPH_IMPORT_DIR`
- `GRAPH_EXPORT_DIR`
- `GRAPH_INSTANCE_ID`
- `GRAPH_DB_VERSION`
- `DIFY_BASE_URL` 或 `DIFY_API_BASE`
- `DIFY_API_KEY`
- `DIFY_TIMEOUT_SECONDS`
- `DIFY_TEXT_INPUT_VARIABLE`
- `DIFY_RESPONSE_MODE`
- `JWT_SECRET`
- `INITIAL_ADMIN_USERNAME`
- `INITIAL_ADMIN_PASSWORD`

## 多实例本地 SQLite 规则

- 主业务数据使用 `SQLITE_PATH`。
- 图谱运行文件使用 `GRAPH_INSTANCE_LOCAL_PATH`。
- 多个实例不能共享同一个 SQLite 图文件。
- 每个实例在启动时从自己的本地图 SQLite 文件加载图数据。
- 如果要统一图版本，应通过导出的 SQLite 图快照分发到各实例。
- 图导入导出是实例级能力，不是全局共享写锁机制。

## 本地联调

```bash
cd /home/Project/AtlasCore
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
```

聊天联调至少需要补齐：

```bash
export DIFY_BASE_URL=https://api.dify.ai/v1
export DIFY_API_KEY=your-dify-api-key
export DIFY_TEXT_INPUT_VARIABLE=query
export DIFY_RESPONSE_MODE=streaming
```

前端联调前至少确认：

```bash
curl -s http://127.0.0.1:${PORT:-8000}/health
curl -s http://127.0.0.1:${PORT:-8000}/health/ready
```

流式聊天联调可额外验证：

```bash
curl -N -H "Content-Type: application/json" \
  -d '{"question":"你好","session_id":null}' \
  http://127.0.0.1:${PORT:-8000}/chat/messages/stream
```

## Azure 联调

- 确认容器监听 `PORT`。
- 将业务 SQLite、图 SQLite、上传目录、导入导出目录挂到实例本地可写路径。
- 配置 `DIFY_BASE_URL`、`DIFY_API_KEY`、`DIFY_TEXT_INPUT_VARIABLE`、`DIFY_RESPONSE_MODE`、管理员认证相关环境变量。
- 使用 `/health` 做平台基础健康检查。
- 使用 `/health/ready` 和 `/api/admin/system/status` 做联调状态检查。
- 不要让多个 Azure 实例共享同一份 `GRAPH_INSTANCE_LOCAL_PATH`。

## 测试

```bash
pytest -q
```

推荐分组：

```bash
pytest -q tests/test_chat_api.py tests/test_dify_client.py
pytest -q tests/test_admin_service.py tests/test_export_api.py tests/test_admin_logs_api.py tests/test_runtime_status.py tests/test_health.py tests/test_admin_system_api.py
pytest -q tests/test_graph_api.py tests/test_graph_file_ops.py tests/test_graph_service.py
```

## 文档

- [deployment.md](/home/Project/AtlasCore/docs/deployment.md)
- [step12_integration.md](/home/Project/AtlasCore/docs/step12_integration.md)
