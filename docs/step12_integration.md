# Step 12 Integration

## 目标

本步骤完成前端、AtlasCore、Dify、SQLite、轻量图模块和多实例本地图 SQLite 机制的联调收口。

## 当前职责边界

- 前端统一调用 AtlasCore。
- AtlasCore 统一封装 Dify 聊天调用。
- AtlasCore 负责问答日志、反馈、CSV 导出、文档管理、图谱查询、图文件导入导出、图重载。
- Dify 负责问答主链路和最终回答。
- 图谱运行依赖本地 SQLite 图文件和 Python 图运行层。

## 联调必查接口

- `GET /health`
- `GET /health/ready`
- `GET /api/admin/system/status`
- `POST /chat/messages`
- `POST /chat/messages/{message_id}/feedback`
- `GET /graph/overview`
- `GET /graph/nodes/{node_id}`
- `GET /graph/nodes/{node_id}/neighbors`
- `GET /graph/subgraph/{node_id}`
- `POST /api/admin/exports/qa-logs`
- `POST /api/admin/exports/feedback`
- `POST /api/admin/graph/export`
- `POST /api/admin/graph/import`
- `POST /api/admin/graph/reload`
- `GET /admin/documents`
- `POST /admin/documents/upload`
- `POST /admin/documents/{document_id}/graph-sync`
- `POST /admin/documents/{document_id}/dify-sync`

## 聊天链路

- 请求流向：Frontend -> AtlasCore `/chat/messages` -> Dify -> AtlasCore -> Frontend
- AtlasCore 会将 `question`、`retrieved_context`、`answer`、`session_id`、`source`、`provider_message_id`、`status`、`error_code` 写入 SQLite。
- 反馈通过 `/chat/messages/{message_id}/feedback` 写入 `feedback_records`。

## 图谱链路

- 请求流向：Frontend -> AtlasCore `/graph/*` -> 本地图 SQLite -> Python 图运行层 -> Frontend
- 返回结构统一补充了 `nodes`、`edges`、`center`、`detail`、`metadata`。
- 管理员图操作全部是实例级操作。

## 文档管理与同步

- `/admin/documents/upload` 记录文档元数据。
- `/admin/documents/{document_id}/graph-sync` 触发图谱同步入口并写入最近同步状态。
- `/admin/documents/{document_id}/dify-sync` 触发 Dify 索引入口并写入最近同步状态。
- 当前版本不引入复杂异步任务系统，但会保留明确状态回执。

## 多实例规则

- `GRAPH_INSTANCE_LOCAL_PATH` 必须指向当前实例自己的本地 SQLite 图文件。
- 多实例不能共享同一个图 SQLite 文件。
- 如果要统一图版本，应将导出的 SQLite 快照分发到每个实例，再分别执行导入/重载。
- 不应把图 SQLite 理解为共享在线写库。

## 状态接口

- `/health` 仅返回 `{"status":"ok"}`。
- `/health/ready` 返回安全摘要，不泄漏 secret。
- `/api/admin/system/status` 返回管理员联调所需状态，包括 Dify、SQLite、图模块、导入导出和实例级路径摘要。

## 关键日志事件

- `chat_request_received`
- `dify_request_started`
- `dify_request_succeeded`
- `dify_request_failed`
- `qa_log_written`
- `feedback_written`
- `graph_query_started`
- `graph_query_succeeded`
- `graph_query_failed`
- `graph_import_started`
- `graph_import_succeeded`
- `graph_import_failed`
- `graph_export_started`
- `graph_export_succeeded`
- `graph_export_failed`
- `csv_export_started`
- `csv_export_succeeded`
- `csv_export_failed`
- `document_sync_started`
- `document_sync_succeeded`
- `document_sync_failed`
- `admin_auth_failed`
