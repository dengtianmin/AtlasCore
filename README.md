# AtlasCore API

AtlasCore 现在处于“Azure 第六步完成”状态：
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
- 导出记录表
- 问答日志 CSV 导出
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

## 5. 最小验证

### Health

```bash
curl -s http://127.0.0.1:${PORT:-8000}/health
```

期望：

```json
{"status":"ok","service":"AtlasCore API"}
```

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

### 导出问答日志 CSV

```bash
curl -s -X POST http://127.0.0.1:${PORT:-8000}/debug/exports/qa-logs \
  -H 'Content-Type: application/json' \
  -d '{"operator":"local-admin"}'
```

结果：
- CSV 文件会写入 `CSV_EXPORT_DIR`
- 导出记录会写入 SQLite 的 `export_records` 表

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
- `app/api/v1/debug.py`
- `config/app.example.yaml`

### 当前核心表
- `admin_accounts`
- `documents`
- `qa_logs`
- `export_records`

## 8. 为后续步骤预留的点

### 第七步预留
- SQLite 路径和导出目录都可通过环境变量注入，适合 App Service
- 导出能力已经有服务层和记录表，可继续接后台管理界面
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
- CSV 导出记录
