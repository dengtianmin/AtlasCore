# Step 12 Integration

## 目标

本步骤完成前端、AtlasCore、Dify、SQLite、轻量图模块和多实例本地图 SQLite 机制的联调收口。

## 当前职责边界

- 前端统一调用 AtlasCore。
- AtlasCore 统一封装 Dify 聊天调用。
- AtlasCore 统一封装评阅 Dify 调用与标准化解析。
- AtlasCore 负责问答日志、评阅日志、反馈、CSV 导出、文档管理、图谱查询、图文件导入导出、图重载。
- Dify 负责问答主链路、评阅 Workflow 和最终回答。
- 图谱运行依赖本地 SQLite 图文件和 Python 图运行层。
- 普通用户必须先注册/登录，才能访问聊天、图谱、评阅功能。
- 管理员后台继续保留独立认证链路。

## 联调必查接口

- `GET /health`
- `GET /health/ready`
- `GET /api/admin/system/status`
- `POST /users/register`
- `POST /users/login`
- `GET /users/me`
- `POST /chat/messages`
- `POST /chat/messages/stream`
- `POST /chat/messages/{message_id}/feedback`
- `POST /review/evaluate`
- `GET /graph/overview`
- `GET /graph/nodes/{node_id}`
- `GET /graph/nodes/{node_id}/neighbors`
- `GET /graph/subgraph/{node_id}`
- `GET /api/admin/review/config`
- `PUT /api/admin/review/config`
- `GET /api/admin/review/logs`
- `POST /api/admin/exports/review-logs`
- `POST /api/admin/exports/qa-logs`
- `POST /api/admin/exports/feedback`
- `POST /api/admin/graph/export`
- `POST /api/admin/graph/import`
- `POST /api/admin/graph/reload`
- `GET /api/admin/documents`
- `POST /api/admin/documents/upload`
- `POST /api/admin/documents/{document_id}/graph-sync`
- `POST /api/admin/documents/{document_id}/dify-sync`

## 聊天链路

- 请求流向：Frontend -> AtlasCore `/chat/messages` -> Dify -> AtlasCore -> Frontend
- 流式请求流向：Frontend -> AtlasCore `/chat/messages/stream` -> Dify streaming -> AtlasCore SSE -> Frontend
- AtlasCore 会将 `question`、`retrieved_context`、`answer`、`session_id`、`source`、`provider_message_id`、`status`、`error_code` 以及普通用户身份快照写入 SQLite。
- 反馈通过 `/chat/messages/{message_id}/feedback` 写入 `feedback_records`。
- 当前前端聊天页默认使用流式接口；`POST /chat/messages` 保留为阻塞式兼容接口。

### 流式事件约定

- AtlasCore 对前端输出 SSE，不直接裸透传 Dify 原始事件。
- `start`：返回 `session_id`、`provider_message_id`、`workflow_run_id`
- `delta`：返回当前文本增量 `text`
- `end`：返回 `message_id`、`session_id`、`status`、`provider_message_id`、`workflow_run_id`、`created_at`
- `error`：返回统一错误字段 `detail`

### Dify 流式联调结论

- 已验证 Dify 当前 Workflow 文本输入变量为 `query`
- 已验证 Dify streaming 会返回 `ping`、`workflow_started`、`node_started`、`node_finished`、`text_chunk`、`workflow_finished`
- Dify 很多事件只有 `data:` 行，事件名放在 JSON 的 `event` 字段内，AtlasCore 当前解析器已兼容该格式

## 评阅链路

- 请求流向：Frontend -> AtlasCore `/review/evaluate` -> Review Dify Workflow -> AtlasCore 标准化层 -> Frontend
- 前端评阅页保持聊天式交互，但 AI 返回的是单条 `review_result` 富消息，而不是纯文本。
- 后端不会把 Dify 原始回包直接透传给前端，而是统一归一化为：
  - `score`
  - `grade`
  - `risk_level`
  - `summary`
  - `review_items`
  - `key_issues`
  - `deduction_logic`
  - `raw_text`
  - `parse_status`
- 评阅日志会绑定普通用户身份快照，并保存原始回包与标准化结果。

### 评阅联调要点

- 聊天 Dify 与评阅 Dify 必须分开配置。
- `REVIEW_DIFY_TEXT_INPUT_VARIABLE` 必须和评阅 Workflow 的真实文本变量名一致，当前推荐为 `query`。
- 当前评阅已允许“评分标准完全内置在 Dify Workflow 中”，本地 rubric 可以为空。
- 评阅 Workflow 的分组输出如 `Group1.output` 已在 AtlasCore 标准化层兼容。

### 评阅管理员接口

- `GET /api/admin/review/config`
- `PUT /api/admin/review/config`
- `GET /api/admin/review/logs`
- `GET /api/admin/review/logs/{record_id}`
- `POST /api/admin/exports/review-logs`

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
- 若聊天接口返回 `Chat integration is not configured`，优先检查 `DIFY_TEXT_INPUT_VARIABLE` 是否已配置，且是否与 Dify Workflow 的真实变量名一致。
- 若评阅接口返回成功但前端无结构化结果，优先检查评阅日志中的 `parse_status`、`raw_output_keys` 与 `dify_text_input_variable`。

## 当前前端入口

- `/login`：普通用户登录
- `/register`：普通用户注册
- `/chat`：普通用户登录后访问
- `/graph`：普通用户登录后访问
- `/review`：普通用户登录后访问
- `/admin/login`：管理员登录

## 关键日志事件

- `chat_request_received`
- `dify_request_started`
- `dify_request_succeeded`
- `dify_request_failed`
- `dify_client_request`
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
- `review_evaluation_started`
- `review_evaluation_completed`
- `review_evaluation_failed`
- `document_sync_started`
- `document_sync_succeeded`
- `document_sync_failed`
- `admin_auth_failed`
