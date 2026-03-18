# AtlasCore Runtime Notes

## Azure App Service 最少检查项

- 确认容器通过 `PORT` 监听。
- `NEXT_PUBLIC_ATLASCORE_API_BASE_URL` 在 Azure 单容器部署里应保持为空，前端走同源 `/api/...`，再由 Next.js rewrite 转发到容器内的 `INTERNAL_API_BASE_URL`。
- `INTERNAL_API_BASE_URL` 保持指向容器内后端，例如 `http://127.0.0.1:8000`。
- 普通用户页面 `/chat`、`/graph`、`/review` 现在要求先登录；部署后需验证 `/login`、`/register` 与普通用户 cookie 链路可用。
- 管理员后台继续使用独立的 `/admin/login` 与管理员 cookie，不与普通用户登录态混用。
- 聊天 Dify 和评阅 Dify 使用独立配置，前端始终只请求 AtlasCore，不直接访问 Dify。
- 使用 `/health` 作为平台基础健康检查。
- 使用 `/health/ready` 查看配置、SQLite、图模块、导入导出摘要。
- 使用 `/api/admin/system/status` 查看管理员联调状态摘要。
- 关注启动日志中的事件：
  - `settings_init`
  - `sqlite_init`
  - `migration_init`
  - `graph_module_check`
  - `graph_load_start`
  - `graph_load_complete`
  - `csv_export_dir_check`
  - `startup_complete`

## SQLite 规则

- `SQLITE_PATH` 和 `GRAPH_INSTANCE_LOCAL_PATH` 必须是实例本地文件。
- 多实例不能共享同一个 SQLite 文件。
- 图版本同步要靠图快照文件分发，不要共享写入单个 `graph.db`。

## 图文件准备

- `GRAPH_IMPORT_DIR`：管理员导入图快照上传目录。
- `GRAPH_EXPORT_DIR`：图快照导出目录。
- `GRAPH_INSTANCE_LOCAL_PATH`：当前实例运行中的图 SQLite 文件。
- `GRAPH_SNAPSHOT_PATH`：可选的图快照路径摘要配置。
- `DIFY_TIMEOUT_SECONDS`：AtlasCore 调用 Dify 聊天接口的超时秒数。

## 评阅 Dify 配置

推荐把评阅接线参数固定到环境变量或密钥管理，不依赖管理员后台在线改动。

建议最少配置：

- `REVIEW_DIFY_BASE_URL`
- `REVIEW_DIFY_API_KEY` 或 `REVIEW_DIFY_API_KEY_SECRET_NAME`
- `REVIEW_DIFY_APP_MODE`
- `REVIEW_DIFY_RESPONSE_MODE`
- `REVIEW_DIFY_TEXT_INPUT_VARIABLE`
- `REVIEW_DIFY_TIMEOUT`
- `REVIEW_DIFY_USER_PREFIX`

推荐值示例：

```env
REVIEW_DIFY_BASE_URL=https://api.dify.ai
REVIEW_DIFY_APP_MODE=workflow
REVIEW_DIFY_RESPONSE_MODE=blocking
REVIEW_DIFY_TEXT_INPUT_VARIABLE=query
REVIEW_DIFY_FILE_INPUT_VARIABLE=
REVIEW_DIFY_TIMEOUT=300
REVIEW_DIFY_ENABLE_TRACE=false
REVIEW_DIFY_USER_PREFIX=review
```

说明：

- `REVIEW_DIFY_BASE_URL` 推荐填写不带 `/v1` 的基础地址。
- `REVIEW_DIFY_TEXT_INPUT_VARIABLE` 必须与评阅 Workflow 的真实文本输入变量名一致。
- 如果评分标准已经内置在 Dify Workflow 中，本地 `review_rubric_settings` 可为空，不影响评阅执行。
- `REVIEW_DIFY_FILE_INPUT_VARIABLE` 当前无文件输入时应保持为空，避免误把文本变量名配置到文件字段。

## 评阅上线前检查

- 管理员登录后检查 `GET /api/admin/review/config`，确认运行时摘要与 `.env` 一致。
- 用普通用户调用一次 `POST /review/evaluate`，确认响应中的 `parse_status` 为 `success` 或 `partial`，而不是 `failed`。
- 如 Dify 端已成功执行但前端无结果，优先检查后端日志中的：
  - `review_evaluation_started`
  - `review_evaluation_completed`
  - `review_evaluation_failed`
- 重点核对日志字段：
  - `dify_text_input_variable`
  - `input_keys`
  - `raw_output_keys`
  - `parse_status`

## 管理员后台能力

- `GET /api/admin/review/config` / `PUT /api/admin/review/config`：查看与调整评阅 Dify 非敏感配置。
- `GET /api/admin/review/logs`：查看评阅日志，包含姓名、学号、评分、风险等级、原始回包与标准化结果。
- `POST /api/admin/exports/review-logs`：导出评阅日志 CSV。

## 运行状态接口

- `/health`：始终返回 `{"status":"ok"}`。
- `/health/ready`：返回安全摘要，不包含 secret 明文。
- `/users/register`、`/users/login`、`/users/me`：普通用户注册、登录与当前身份接口。
- `/review/evaluate`：普通用户评阅接口，返回统一 `review_result` 结构。
- `/api/admin/review/config`、`/api/admin/review/logs`：评阅后台配置与日志接口。
