# AtlasCore

AtlasCore 是一个 SQLite-first 的 FastAPI 后端，负责系统 API、管理员能力、图谱 API、日志与导出。Dify 继续负责问答主链路；当前运行前提不是 Neo4j 或 PostgreSQL。

当前仓库已完成“步骤十一：完善应用配置、启动参数、健康检查、日志、导入导出与实例运行规则”。

## 当前架构边界

- Dify 负责问答主链路和答案生成。
- AtlasCore 负责系统后端、管理员能力、图谱 API、日志与导出。
- 主业务存储使用 `SQLITE_PATH` 指向的 SQLite 文件。
- 图谱底层使用 `GRAPH_INSTANCE_LOCAL_PATH` 指向的本地 SQLite 文件，加 Python 图运行层。
- `NEO4J_*` 仅保留为未来预留项，不是当前运行依赖。

## 步骤十一完成内容

- 统一应用配置与启动参数读取。
- 启动阶段日志增强，补充结构化初始化事件。
- `GET /health` 轻量健康检查。
- `GET /health/ready` 安全状态检查。
- 图导入导出与 CSV 导出的运行诊断增强。
- 运行时状态聚合服务，集中提供启动、图加载、导入导出摘要。
- 明确多实例本地 SQLite 运行规则。

## 关键环境变量

基础运行配置：

- `APP_NAME`
- `APP_ENV`
- `PORT`
- `LOG_LEVEL`
- `APP_CONFIG_PATH`

SQLite / 业务数据配置：

- `SQLITE_PATH`
- `CSV_EXPORT_DIR`
- `DOCUMENT_LOCAL_STORAGE_DIR`

图模块配置：

- `GRAPH_ENABLED`
- `GRAPH_DEFAULT_LIMIT`
- `GRAPH_MAX_NEIGHBORS`
- `GRAPH_RELOAD_ON_START`
- `GRAPH_INSTANCE_LOCAL_PATH`
- `GRAPH_IMPORT_DIR`
- `GRAPH_EXPORT_DIR`
- `GRAPH_SNAPSHOT_PATH`
- `GRAPH_INSTANCE_ID`
- `GRAPH_DB_VERSION`

外部集成与认证：

- `DIFY_BASE_URL` 或 `DIFY_API_BASE`
- `DIFY_API_KEY`
- `JWT_SECRET`
- `INITIAL_ADMIN_USERNAME`
- `INITIAL_ADMIN_PASSWORD`
- `ADMIN_AUTH_SECRET`
- `ADMIN_PASSWORD_HASH`

说明：

- secret 只做“是否已配置”检查，不会出现在日志或状态接口里。
- 启动时会自动创建目录型路径，并对关键路径做基础可读写检查。

## 健康检查与状态检查

`GET /health`

- 用途：App Service 基础健康检查。
- 行为：始终轻量，固定返回 `200 OK`。
- 响应：

```json
{"status":"ok"}
```

`GET /health/ready`

- 用途：运维排障、实例 readiness 判断。
- 行为：返回安全摘要，不泄漏 secret。
- 关键字段：
  - `config_loaded`
  - `sqlite_ready`
  - `migration_ready`
  - `graph_enabled`
  - `graph_loaded`
  - `graph_node_count`
  - `graph_edge_count`
  - `graph_instance_id`
  - `graph_db_version`
  - `graph_instance_local_path_exists`
  - `graph_import_dir_readable`
  - `graph_export_dir_writable`
  - `csv_export_dir_writable`
  - `dify_configured`
  - `admin_auth_configured`
  - `started_at`
  - `uptime_seconds`

## 多实例本地 SQLite 运行规则

- 主业务 SQLite 使用 `SQLITE_PATH`。
- 图实例 SQLite 使用 `GRAPH_INSTANCE_LOCAL_PATH`。
- 多实例不能共享同一个 SQLite 文件。
- 每个实例都必须有独立的 `GRAPH_INSTANCE_ID`。
- 若需要统一图版本，应分发统一导出的 SQLite 图快照，而不是多实例共享写同一个 `graph.db`。
- 实例启动时从本地图文件加载图数据。
- 图更新方式应为：
  - 导入新的 SQLite 图文件；
  - 替换本地图文件后 reload；
  - 或随镜像分发新的本地图文件。

## 本地运行

```bash
cd /home/Project/AtlasCore
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
```

默认健康检查：

```bash
curl -s http://127.0.0.1:${PORT:-8000}/health
curl -s http://127.0.0.1:${PORT:-8000}/health/ready
```

## Docker / Azure App Service

[Dockerfile](/home/Project/AtlasCore/Dockerfile) 默认通过 `PORT` 启动：

```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

部署到 Azure App Service 时至少关注：

- 容器实际监听端口是否与 `PORT` 一致。
- `/health` 用于平台基础健康检查。
- `/health/ready` 用于运行状态与实例排障。
- 容器日志中可查看启动阶段事件、SQLite 初始化、graph load、导入导出结果。
- 需要提前准备本地目录：
  - `CSV_EXPORT_DIR`
  - `GRAPH_IMPORT_DIR`
  - `GRAPH_EXPORT_DIR`
  - `GRAPH_INSTANCE_LOCAL_PATH` 的父目录
- 不要让多个实例共享同一个 SQLite 或 graph SQLite 文件。

## 测试

局部测试：

```bash
pytest -q tests/test_config.py tests/test_runtime_status.py
pytest -q tests/test_lifespan.py tests/test_main.py
pytest -q tests/test_health.py
pytest -q tests/test_graph_file_ops.py tests/test_export_api.py tests/test_graph_service.py tests/test_graph_api.py
pytest -q tests/test_logging_safety.py
```

完整测试：

```bash
pytest -q
```

## 排障提示

- `config_error`：优先检查环境变量、`APP_CONFIG_PATH`、secret 配置状态。
- `sqlite_init_error`：优先检查 `SQLITE_PATH` 父目录权限。
- `graph_load_error`：优先检查 `GRAPH_INSTANCE_LOCAL_PATH` 是否存在、graph SQLite 表结构是否完整。
- `graph_import_error`：优先检查导入文件是否为合法 SQLite 图快照。
- `graph_export_error`：优先检查 graph SQLite 文件是否存在、导出目录是否可写。
- `csv_export_error`：优先检查 `CSV_EXPORT_DIR` 和业务 SQLite 连接状态。
