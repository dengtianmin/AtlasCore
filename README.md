# AtlasCore

AtlasCore 当前同时包含：
- FastAPI 后端：管理员认证、文档管理、图谱浏览、问答日志、反馈与 CSV 导出
- Next.js 前端：工作台、聊天页、图谱页、管理员后台

AtlasCore 现在处于“Azure 第七步完成”状态：
- Dify 仍负责知识库问答主链路和最终答案生成
- AtlasCore 负责管理员认证、文档元数据、图谱接口占位、问答日志、反馈/导出基础能力
- 运行期主存储为 SQLite
- 导出格式为 CSV
- Neo4j / Dify / JWT 敏感配置继续通过环境变量预留，不在这一步做完整接入

## 1. 当前架构边界

### 本步已完成
- 统一配置加载：环境变量 + YAML/JSON 初始化配置文件
- SQLite-first 数据层
- 启动时自动建表
- 可选的初始管理员初始化
- 文档元数据表
- 问答日志表
- 反馈记录表
- 导出记录表
- 问答日志 CSV 导出
- 面向未来前端的导出触发、列表、下载 API
- 最小验证接口

### 本步明确不做
- 普通用户登录
- 多角色权限系统
- 基础 RAG 主链路迁入 AtlasCore
- 完整 Neo4j 接入
- 完整 Dify API 联调
- Key Vault / Managed Identity
- 多实例并发写同一 SQLite

## 2. 配置职责

### 配置文件字段
配置文件只放初始化和非敏感默认配置，示例见 [config/app.example.yaml](config/app.example.yaml)。

主要包括：
- `app.*`
  - 服务名、默认端口、日志级别、API 前缀
- `admin.initial_username`
  - 初始管理员用户名
- `defaults.page`
  - 页面默认配置
- `defaults.features`
  - 功能开关
- `defaults.mappings`
  - 固定映射项
- `export.rules`
  - 导出规则占位
- `integrations.*`
  - Neo4j / Dify / JWT 的非敏感占位配置

### 环境变量字段
环境变量负责运行环境差异和敏感项：

| 变量 | 说明 | 这一步是否使用 |
|---|---|---|
| `APP_CONFIG_PATH` | YAML/JSON 配置文件路径 | 是 |
| `SQLITE_PATH` | SQLite 文件路径 | 是 |
| `CSV_EXPORT_DIR` | CSV 导出目录 | 是 |
| `DOCUMENT_LOCAL_STORAGE_DIR` | 本地文档上传目录 | 是 |
| `INITIAL_ADMIN_PASSWORD` | 初始管理员密码 | 是，且必须走环境变量 |
| `JWT_SECRET` | JWT 密钥 | 是 |
| `NEO4J_URI` / `NEO4J_USERNAME` / `NEO4J_PASSWORD` / `NEO4J_DATABASE` | Neo4j 预留配置 | 仅预留 |
| `DIFY_BASE_URL` / `DIFY_API_KEY` | Dify 预留配置 | 仅预留 |

说明：
- 初始管理员用户名可以放配置文件。
- 初始管理员密码不写入配置文件，避免明文落盘。
- 这一步不要求设置 Neo4j / Dify 环境变量，保留给后续步骤。

## 3. 数据职责

### SQLite 职责
- 作为单实例 AtlasCore 的运行期主存储
- 保存管理员账号、文档元数据、问答日志、导出记录
- 保存独立反馈记录
- 适合 Azure App Service 第七步前的轻量部署方式

### CSV 职责
- 作为导出分析格式，不是在线主存储
- 当前已支持导出问答日志
- 后续可继续扩展到文档元数据、用户反馈、图谱同步记录

### 为什么当前保持单实例
- SQLite 更适合单实例本地文件写入
- 这一步目标是先完成“可运行、可导出、可继续演进”的基础设施
- 多实例写冲突、任务调度、分布式锁都不在当前阶段范围内

## 4. 本地运行

### 安装依赖

```bash
cd /home/Project/AtlasCore
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 推荐环境变量

```bash
export APP_CONFIG_PATH=/home/Project/AtlasCore/config/app.example.yaml
export SQLITE_PATH=/home/Project/AtlasCore/data/atlascore.db
export CSV_EXPORT_DIR=/home/Project/AtlasCore/data/exports
export DOCUMENT_LOCAL_STORAGE_DIR=/home/Project/AtlasCore/data/uploads
export INITIAL_ADMIN_PASSWORD='StrongPass123!'
export JWT_SECRET='local-dev-secret'
```

可选：

```bash
export PORT=8000
export APP_ENV=development
```

### 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
```

## 5. 前端运行

前端代码位于 [frontend/package.json](frontend/package.json)。

### 安装前端依赖

```bash
cd /home/Project/AtlasCore/frontend
npm install
```

### 配置前端 API 地址

```bash
cd /home/Project/AtlasCore/frontend
cat <<'EOF' > .env.local
NEXT_PUBLIC_ATLASCORE_API_BASE_URL=http://127.0.0.1:8000
EOF
```

### 启动前端

```bash
cd /home/Project/AtlasCore/frontend
npm run dev
```

默认访问：
- `http://127.0.0.1:3000/`
- 管理员登录页：`http://127.0.0.1:3000/admin/login`

## 6. 前端页面与接口对齐

当前前端已实现：
- `/` 轻量工作台
- `/chat` 聊天页，对接 `POST /chat/messages`
- `/graph` 图谱页，对接 `/graph/*`
- `/admin/login` 管理员登录页，对接 `/auth/login`
- `/admin` 后台总览页
- `/admin/documents` 文档管理页，对接 `/admin/documents*`
- `/admin/logs` 问答日志页，对接 `/api/admin/logs*`
- `/admin/exports` 导出管理页，对接 `/api/admin/exports*`

新增的前端适配后端接口：
- `POST /chat/messages`
- `POST /chat/messages/{message_id}/feedback`
- `GET /api/admin/logs`
- `GET /api/admin/logs/{record_id}`

## 7. 最小验证

### Health

```bash
curl -s http://127.0.0.1:${PORT:-8000}/health
```

期望：

```json
{"status":"ok","service":"AtlasCore API"}
```

### 聊天接口

```bash
curl -s -X POST http://127.0.0.1:${PORT:-8000}/chat/messages \
  -H 'Content-Type: application/json' \
  -d '{
    "question":"AtlasCore 是什么？"
  }'
```

说明：
- 当前返回 AtlasCore 占位答复
- 该接口已经用于前端聊天页联调
- 后续可在此处接入真实 Dify 聊天转发

### 写入一条问答日志

```bash
curl -s -X POST http://127.0.0.1:${PORT:-8000}/debug/qa-logs \
  -H 'Content-Type: application/json' \
  -d '{
    "question":"AtlasCore 是什么？",
    "retrieved_context":"AtlasCore 是 Azure 后端层。",
    "answer":"AtlasCore 是负责系统层能力的后端。",
    "rating":5,
    "liked":true,
    "session_id":"demo-session",
    "source":"dify"
  }'
```

### 查询问答日志

```bash
curl -s http://127.0.0.1:${PORT:-8000}/debug/qa-logs
```

### 写入反馈记录

```bash
curl -s -X POST http://127.0.0.1:${PORT:-8000}/debug/qa-logs/<qa_log_id>/feedback \
  -H 'Content-Type: application/json' \
  -d '{
    "rating":5,
    "liked":true,
    "comment":"回答有帮助",
    "source":"anonymous"
  }'
```

### 查询问答日志对应反馈

```bash
curl -s http://127.0.0.1:${PORT:-8000}/debug/qa-logs/<qa_log_id>/feedback
```

### 访问 root 调试入口

```bash
curl -s http://127.0.0.1:${PORT:-8000}/
```

返回：
- `health_url`
- 未来前端可调用的导出接口地址
- 最近一次导出文件的下载地址

### 管理员登录验证

```bash
curl -s -X POST http://127.0.0.1:${PORT:-8000}/auth/login \
  -H 'Content-Type: application/json' \
  -d '{
    "username":"admin",
    "password":"StrongPass123!"
  }'
```

说明：
- `admin` 来自示例配置文件中的 `admin.initial_username`
- 密码来自环境变量 `INITIAL_ADMIN_PASSWORD`

把响应里的 `access_token` 保存为环境变量：

```bash
export ACCESS_TOKEN='<your-access-token>'
```

### 触发正式导出 API

```bash
curl -s -X POST http://127.0.0.1:${PORT:-8000}/api/admin/exports/qa-logs \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{"operator":"local-admin"}'
```

期望：
- CSV 文件写入 `CSV_EXPORT_DIR`
- 导出记录写入 SQLite 的 `export_records` 表
- 返回 `filename` 和 `download_url`

### 查询导出列表

```bash
curl -s http://127.0.0.1:${PORT:-8000}/api/admin/exports \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

### 查询正式日志接口

```bash
curl -s http://127.0.0.1:${PORT:-8000}/api/admin/logs \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

### 下载导出的 CSV

```bash
curl -OJ http://127.0.0.1:${PORT:-8000}/api/admin/exports/download/<filename> \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

## 8. 本地联调建议

1. 先启动后端 `uvicorn app.main:app --host 0.0.0.0 --port 8000`
2. 再启动前端 `cd frontend && npm run dev`
3. 访问 `/admin/login`，使用 `admin` 与 `INITIAL_ADMIN_PASSWORD` 登录
4. 在 `/chat` 验证聊天与反馈
5. 在 `/graph` 验证图谱浏览与节点详情
6. 在 `/admin/documents` 验证上传、删除与同步按钮
7. 在 `/admin/logs` 验证日志筛选与详情
8. 在 `/admin/exports` 验证导出与下载

## 9. 部署说明

第一版建议沿用“前后端并行部署”的 Azure 结构：
- AtlasCore API 作为后端服务继续部署
- Next.js 前端单独部署，并通过 `NEXT_PUBLIC_ATLASCORE_API_BASE_URL` 指向后端

这样可以保持架构边界清晰：
- 前端只调用 AtlasCore
- AtlasCore 内部负责 Dify 与后续 Neo4j 扩展
- 不需要为了第一版引入复杂微前端或额外中间层

### 兼容的 debug 导出接口

```bash
curl -s -X POST http://127.0.0.1:${PORT:-8000}/debug/exports/qa-logs \
  -H 'Content-Type: application/json' \
  -d '{"operator":"local-admin"}'
```

这个接口继续保留给联调和本地验证使用，但未来前端应优先接 `/api/admin/exports/*`。

## 6. Docker 运行

### 构建镜像

```bash
docker build -t atlascore-api:local .
```

### 运行容器

```bash
docker run --rm -p 8000:8000 \
  -e PORT=8000 \
  -e APP_CONFIG_PATH=/app/config/app.example.yaml \
  -e SQLITE_PATH=/app/data/atlascore.db \
  -e CSV_EXPORT_DIR=/app/data/exports \
  -e DOCUMENT_LOCAL_STORAGE_DIR=/app/data/uploads \
  -e INITIAL_ADMIN_PASSWORD='StrongPass123!' \
  -e JWT_SECRET='local-dev-secret' \
  atlascore-api:local
```

容器默认路径：
- SQLite: `/app/data/atlascore.db`
- CSV 导出: `/app/data/exports`
- 上传目录: `/app/data/uploads`

这些路径都可以被环境变量覆盖，适合后续迁移到 Azure App Service 挂载目录。

## 7. 关键文件

### 核心代码目录
- `app/core/config.py`
- `app/core/lifespan.py`
- `app/db/session.py`
- `app/models/`
- `app/repositories/`
- `app/services/`
- `app/api/v1/admin_exports.py`
- `app/api/v1/root.py`
- `app/api/v1/debug.py`
- `config/app.example.yaml`
- `alembic/env.py`

### 当前核心表
- `admin_accounts`
- `documents`
- `qa_logs`
- `feedback_records`
- `export_records`

## 8. 为后续步骤预留的点

### 第七步预留
- SQLite 路径和导出目录都可通过环境变量注入，适合 App Service
- 导出能力已经有服务层和记录表，可继续接后台管理界面
- 未来前端按钮可以先调用 `POST /api/admin/exports/qa-logs`
- 然后直接使用返回值中的 `download_url`
- 或从 `GET /api/admin/exports` 列表里读取 `download_url`
- 启动期初始化逻辑已具备，可继续加更正式的 bootstrap/migration 流程

### 第八步预留
- `NEO4J_*` 配置仍保留
- `/graph/*` 路由和 graph service 仍在
- 当前只做接口占位，不做真实图库接入与同步链路

### 仍未完成
- 真实 Dify API 联调
- 图谱真实同步状态管理
- Key Vault / Managed Identity
- 多实例共享存储与并发写控制

## 9. 测试

运行全量测试：

```bash
pytest -q
```

当前基线覆盖：
- 配置加载
- SQLite 初始化与启动生命周期
- 管理员密码/JWT
- 文档管理服务
- 问答日志写入与查询
- 独立反馈记录写入与查询
- CSV 导出记录
