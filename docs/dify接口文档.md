# Dify 接口整理（AtlasCore 联调版）

## 1. 文档目的

本文档用于整理 **AtlasCore 与 Dify 后端联调** 时真正需要关注的 Dify 接口、请求参数、返回结构、推荐调用方式与配置项。

本文档不追求覆盖 Dify 所有能力，而是从当前项目的实际架构出发进行筛选：

- 前端统一调用 AtlasCore
- AtlasCore 内部转发 Dify
- 图谱链路由 AtlasCore + SQLite + Python 图模块承担
- Dify 主要负责知识库问答与 Workflow 执行

因此，本文重点围绕以下场景展开：

1. 聊天问答主链路
2. 评阅 Workflow 主链路
3. 文档上传 / 文件型输入
4. Workflow 执行状态查询
5. 流式任务停止
6. 应用参数读取
7. 日志排查与联调辅助

---

## 2. 基础信息

### 2.1 Base URL

```text
https://api.dify.ai/v1
```

### 2.2 认证方式

Dify Service API 使用 API Key 鉴权。

请求头格式：

```http
Authorization: Bearer {API_KEY}
```

### 2.3 使用建议

- API Key 必须保存在 AtlasCore 后端，不应暴露到前端
- 前端不直接调用 Dify
- 所有对 Dify 的调用统一经由 AtlasCore 转发
- AtlasCore 负责超时控制、错误处理、日志记录和统一返回结构

---

## 3. 当前项目与 Dify 的交互边界

### 3.1 Dify 负责什么

- Workflow 编排
- 知识库问答
- 文档解析 / 切分 / 检索
- 模型调用
- Prompt / Workflow 运行

### 3.2 AtlasCore 负责什么

- 对前端暴露统一聊天接口
- 对前端暴露统一评阅接口
- 对前端隐藏 Dify 细节
- 记录问答日志、评阅日志、召回内容、回答结果、评分与反馈
- 对评阅结果做标准化，不把 Dify 原始回包直接透传前端
- 处理管理员文档同步动作
- 承担健康检查、系统状态和联调观测

### 3.3 当前项目最相关的 Dify 接口

按优先级排序，当前项目最相关的接口为：

1. `POST /workflows/run`
2. `POST /workflows/{workflow_id}/run`
3. `POST /files/upload`
4. `GET /workflows/run/{workflow_run_id}`
5. `POST /workflows/tasks/{task_id}/stop`
6. `GET /parameters`
7. `GET /workflows/logs`
8. `GET /info`

其中前 4 个是主链路必需接口，后 4 个更偏配置读取、调试与运维辅助。

---

## 4. 核心接口一：执行当前已发布 Workflow

### 4.1 接口

```http
POST /workflows/run
```

### 4.2 用途

执行当前已发布的 Workflow。

这是 AtlasCore 聊天主链路最重要的接口，通常由：

- `POST /chat/messages`
- 某些管理员测试接口
- 某些联调验证接口

在后端内部调用。

### 4.3 请求体核心字段

```json
{
  "inputs": {},
  "response_mode": "blocking",
  "user": "abc-123",
  "trace_id": "optional-trace-id"
}
```

字段说明：

#### `inputs`（必填）

Workflow 输入变量对象。

- key 为 Workflow 变量名
- value 为该变量对应值
- 支持普通文本变量
- 也支持文件列表变量

#### `response_mode`（必填）

支持两种模式：

- `blocking`：阻塞模式，等待执行完成后直接返回完整结果
- `streaming`：流式模式，基于 SSE 逐块返回事件

当前项目建议：

- AtlasCore 当前版本已同时支持 `blocking` 与 `streaming`
- 前端聊天页默认走 AtlasCore 流式接口，再由 AtlasCore 对接 Dify `streaming`
- 若只做后端兼容验证，可继续使用 `blocking`

#### `user`（必填）

终端用户标识。

要求：

- 在应用内唯一
- 由 AtlasCore 自己生成或管理
- 不要求与 WebApp 会话一致

当前项目建议：

- 匿名普通用户：使用 `guest-{session_id}`
- 管理员测试：使用 `admin-{username}` 或固定调试前缀

#### `trace_id`（可选）

链路追踪 ID，用于把 Dify 调用和 AtlasCore 的日志体系打通。

建议：

- AtlasCore 为每个外部请求生成统一 trace_id
- 同时传给自己的日志系统和 Dify

### 4.4 推荐调用场景

AtlasCore 中最典型的映射方式：

前端调用：

```text
POST /chat/messages
```

AtlasCore 内部转成：

```json
{
  "inputs": {
    "query": "用户问题文本"
  },
  "response_mode": "blocking",
  "user": "guest-xxxx",
  "trace_id": "trace-xxxx"
}
```

> 注意：`query` 只是示例变量名，实际变量名必须与你在 Dify Workflow 中定义的一致。

对于当前项目的评阅链路，推荐固定：

- `REVIEW_DIFY_APP_MODE=workflow`
- `REVIEW_DIFY_RESPONSE_MODE=blocking`
- `REVIEW_DIFY_TEXT_INPUT_VARIABLE=query`

如果后台把文本变量名误配到 `REVIEW_DIFY_FILE_INPUT_VARIABLE`，AtlasCore 当前版本会做有限兜底；但规范做法仍然是把真实文本变量名放在 `REVIEW_DIFY_TEXT_INPUT_VARIABLE`。

### 4.5 blocking 模式返回结构

成功时通常返回：

```json
{
  "workflow_run_id": "xxx",
  "task_id": "xxx",
  "data": {
    "id": "xxx",
    "workflow_id": "xxx",
    "status": "succeeded",
    "outputs": {
      "text": "Nice to meet you."
    },
    "error": null,
    "elapsed_time": 0.875,
    "total_tokens": 3562,
    "total_steps": 8,
    "created_at": 1705407629,
    "finished_at": 1727807631
  }
}
```

AtlasCore 需要重点提取：

- `workflow_run_id`
- `task_id`
- `data.status`
- `data.outputs`
- `data.error`
- `data.elapsed_time`
- `data.total_tokens`

### 4.6 AtlasCore 应该如何处理返回

建议 AtlasCore 内部做以下转换：

#### 成功时

返回前端统一结构，例如：

```json
{
  "message_id": "atlas-msg-001",
  "answer": "...",
  "source": "dify",
  "workflow_run_id": "...",
  "elapsed_time": 0.875,
  "status": "succeeded"
}
```

#### 失败时

记录：

- Dify 错误码
- 错误消息
- workflow_run_id（若有）
- task_id（若有）
- trace_id

并返回 AtlasCore 自己的错误格式，而不是把 Dify 原始报文直接透给前端。

### 4.8 评阅 Workflow 输出约定

评阅接口 `POST /review/evaluate` 走的是独立 Review Dify Workflow。对于评阅链路，AtlasCore 当前会优先把 Dify 输出标准化为统一的 `review_result` 结构：

```json
{
  "type": "review_result",
  "score": 82,
  "grade": "良好",
  "risk_level": "medium",
  "summary": "方案内容完整，但存在需复核项。",
  "review_items": [],
  "key_issues": [],
  "deduction_logic": [],
  "raw_text": null,
  "parse_status": "success"
}
```

当前已兼容的原始输出形态包括：

- 顶层直接返回评阅 JSON
- `result`
- `data`
- `outputs`
- `review_result`
- `output`
- Workflow 分组输出，例如 `Group1.output`

如果 Dify 已成功执行，但 AtlasCore 日志中的 `parse_status` 仍为 `failed`，优先检查：

- 结构化结果是否被包在多层嵌套里
- `score`、`summary`、`review_items` 等字段名是否被改名
- 工作流是否只返回了 Markdown 文本，而没有任何 JSON

### 4.7 常见错误

文档中列出的常见错误包括：

- `invalid_param`
- `app_unavailable`
- `provider_not_initialize`
- `provider_quota_exceeded`
- `model_currently_not_support`
- `workflow_request_error`
- `500` 内部服务异常

AtlasCore 侧建议分类处理：

- 参数错误：返回 4xx 给前端
- Dify 配置错误：作为系统告警
- 模型额度不足：返回“服务暂不可用”
- Workflow 执行失败：写入日志，便于后台排查

---

## 5. 核心接口二：执行指定版本 Workflow

### 5.1 接口

```http
POST /workflows/{workflow_id}/run
```

### 5.2 用途

执行指定版本的 Workflow。

相比 `/workflows/run`，这个接口更适合：

- dev / test / prod 多环境固定版本
- 管理员联调指定版本
- 避免“当前已发布版本”变化导致线上行为漂移

### 5.3 适用建议

当前项目建议：

- 第一阶段联调先接 `POST /workflows/run`
- 第二阶段再引入 `DIFY_WORKFLOW_ID`
- 需要版本稳定性时，再切到 `POST /workflows/{workflow_id}/run`

### 5.4 额外错误

除通用错误外，还可能出现：

- `workflow_not_found`
- `draft_workflow_error`
- `workflow_id_format_error`

所以一旦启用该接口，AtlasCore 启动时最好主动校验：

- workflow_id 是否配置
- workflow_id 格式是否正确
- workflow 对应版本是否存在

---

## 6. 核心接口三：上传文件

### 6.1 接口

```http
POST /files/upload
```

### 6.2 用途

上传文件并在 Workflow 中作为文件型输入使用。

适合当前项目中的场景：

- 管理员上传文档后触发 Dify 文档处理
- 文件型问答输入
- 文档和文本混合理解

### 6.3 请求方式

必须使用 `multipart/form-data`。

核心字段：

- `file`：上传的文件
- `user`：终端用户标识

### 6.4 示例

```bash
curl -X POST 'https://api.dify.ai/v1/files/upload' \
--header 'Authorization: Bearer {api_key}' \
--form 'file=@localfile;type=image/png' \
--form 'user=abc-123'
```

### 6.5 成功返回

```json
{
  "id": "72fa9618-8f89-4a37-9b33-7e1178a24a67",
  "name": "example.png",
  "size": 1024,
  "extension": "png",
  "mime_type": "image/png",
  "created_by": 123,
  "created_at": 1577836800
}
```

AtlasCore 需要重点保存：

- `id`（即 `upload_file_id`）
- 文件名
- 文件大小
- MIME 类型
- 上传时间

### 6.6 与 Workflow 的联动方式

上传成功后，文件型变量可这样传入 Workflow：

```json
{
  "inputs": {
    "orig_mail": [
      {
        "transfer_method": "local_file",
        "upload_file_id": "{file_id}",
        "type": "document"
      }
    ]
  },
  "response_mode": "blocking",
  "user": "difyuser"
}
```

### 6.7 当前项目中的推荐用法

管理员文档上传链路建议拆成两段：

#### 第一步：上传到 AtlasCore

- 前端上传文档到 AtlasCore
- AtlasCore 保存文档元数据
- AtlasCore 记录内部 document_id

#### 第二步：同步到 Dify

- AtlasCore 调用 `POST /files/upload`
- 拿到 `upload_file_id`
- 更新文档表中的 Dify 同步状态
- 必要时再调用 Workflow

### 6.8 常见错误

- `no_file_uploaded`
- `too_many_files`
- `unsupported_preview`
- `unsupported_estimate`
- `file_too_large`
- `unsupported_file_type`
- `s3_connection_failed`
- `s3_permission_denied`
- `s3_file_too_large`

AtlasCore 侧建议：

- 提前校验文件大小与扩展名
- 统一限制可上传类型
- 失败时把 Dify 错误写入 `documents.note` 或同步记录表

---

## 7. 核心接口四：查询 Workflow 执行状态

### 7.1 接口

```http
GET /workflows/run/{workflow_run_id}
```

### 7.2 用途

按 `workflow_run_id` 查询某次 Workflow 执行状态。

### 7.3 适用场景

适合当前项目中的这些情况：

- streaming 模式下轮询补查最终状态
- 管理员查看某次任务是否成功
- 联调时复盘一次失败执行
- AtlasCore 自己的异步补偿任务查询结果

### 7.4 返回重点字段

```json
{
  "id": "...",
  "workflow_id": "...",
  "status": "succeeded",
  "inputs": "...",
  "outputs": null,
  "error": null,
  "total_steps": 3,
  "total_tokens": 0,
  "created_at": 1705407629,
  "finished_at": 1727807631,
  "elapsed_time": 30.0985
}
```

重点关注：

- `status`
- `outputs`
- `error`
- `total_steps`
- `total_tokens`
- `elapsed_time`

### 7.5 当前项目建议

如果第一阶段只用 `blocking`，这个接口不是绝对必需。

但建议仍然封装好，因为它对：

- 排障
- 后台状态展示
- 未来异步执行

都很有帮助。

---

## 8. 核心接口五：停止流式任务

### 8.1 接口

```http
POST /workflows/tasks/{task_id}/stop
```

### 8.2 用途

停止一个正在执行的流式任务。

### 8.3 限制

- **仅支持 streaming 模式**
- `user` 必须与启动任务时使用的 `user` 保持一致

### 8.4 请求体

```json
{
  "user": "abc-123"
}
```

### 8.5 返回

```json
{
  "result": "success"
}
```

### 8.6 当前项目建议

当前阶段如果聊天先走 `blocking`，可以暂时不接这个接口。

如果后续改成：

- 页面实时流式输出
- 用户支持“停止生成”

那么这个接口必须接入。

---

## 9. 核心接口六：获取应用参数

### 9.1 接口

```http
GET /parameters
```

### 9.2 用途

读取 Dify 应用的参数定义，用于了解：

- 有哪些输入变量
- 变量名是什么
- 哪些字段必填
- 是否支持文件上传
- 文件类型和数量限制是什么
- 文件大小限制是什么

### 9.3 为什么这个接口很重要

在当前项目里，Dify 最容易联调失败的地方不是 URL，也不是 API Key，而是：

- Workflow 输入变量名不匹配
- 文件变量名不匹配
- 文件类型或数量不符合限制
- AtlasCore 以为某字段是必填，实际不是
- AtlasCore 以为某变量名是 `query`，实际 Dify 定义成了别的名字

因此，`GET /parameters` 是 **强烈建议接入的校验接口**。

### 9.4 返回重点

通常包含：

- `user_input_form`
- `file_upload`
- `system_parameters`

例如可以得到：

- 文本输入控件的 `variable`
- 是否必填 `required`
- 文件类型是否启用
- 文件数量限制 `number_limits`
- 文件大小限制 `file_size_limit`

### 9.5 当前项目中的推荐用法

建议至少两种使用方式：

#### 启动时校验

AtlasCore 启动后主动读取一次 `/parameters`，检查：

- 配置的文本变量名是否存在
- 配置的文件变量名是否存在
- 文件能力是否启用

#### 管理员诊断接口

可以在管理员系统状态页展示：

- 当前 Dify 配置是否可用
- 当前 Workflow 允许哪些输入变量
- 当前文件上传限制是什么

---

## 10. 辅助接口：获取 Workflow 日志

### 10.1 接口

```http
GET /workflows/logs
```

### 10.2 用途

倒序获取 Workflow 日志。

支持按这些条件筛选：

- `keyword`
- `status`
- `page`
- `limit`
- `created_by_end_user_session_id`
- `created_by_account`

### 10.3 适用场景

这个接口不一定进入前台主链路，但很适合：

- 联调排查
- 管理员后台诊断
- 复核 Dify 是否真的收到请求
- 对账 AtlasCore 日志与 Dify 执行记录

### 10.4 当前项目建议

作为管理员联调辅助能力接入，而不是普通用户能力。

---

## 11. 辅助接口：获取应用基本信息

### 11.1 接口

```http
GET /info
```

### 11.2 用途

获取 Dify 应用基础信息，例如：

- 应用名称
- 描述
- 标签
- 模式
- 作者名称

### 11.3 当前项目建议

不是主链路必需，但可以用于：

- AtlasCore 启动时自检
- 管理员系统状态页展示当前绑定的是哪个 Dify 应用

---

## 12. 返回模式：blocking 与 streaming 的选择建议

### 12.1 blocking

优点：

- 后端实现最简单
- AtlasCore 最容易统一处理
- 前端最容易接入

缺点：

- 长流程可能超时
- 无法实时展示生成内容
- Cloudflare 限制下超过 100 秒可能中断

### 12.2 streaming

优点：

- 可以实时返回文本片段
- 可展示节点级执行过程
- 更适合复杂长流程

缺点：

- AtlasCore 需要支持 SSE 转发或流式聚合
- 错误处理更复杂
- 如果前端暂时不做打字机输出，收益不大

### 12.3 当前项目建议

- AtlasCore 已落地 `streaming` 主链路，前端聊天页默认使用流式输出
- `blocking` 仍保留，适合脚本调用、故障排查和最小兼容集成
- 若遇到 `Chat integration is not configured`，优先检查 `DIFY_TEXT_INPUT_VARIABLE`

---

## 13. streaming 模式下的事件结构

如果后续启用流式模式，AtlasCore 需要理解以下事件：

### 13.1 `workflow_started`

表示整个 Workflow 开始执行。

### 13.2 `node_started`

表示某个节点开始执行。

可用于：

- Tracing 展示
- 调试执行路径

### 13.3 `text_chunk`

表示生成了一段文本。

这是前端实时显示答案的关键事件。

### 13.4 `node_finished`

表示某个节点执行完成。

可以拿到：

- 节点输入
- 节点输出
- 执行状态
- token / price 等元数据

### 13.5 `workflow_finished`

表示整个 Workflow 执行完成。

### 13.6 `tts_message` / `tts_message_end`

用于语音合成输出。

当前项目如果没有 TTS 页面能力，可以先忽略。

### 13.7 `ping`

保活事件，用于保持连接。

### 13.8 当前项目已验证的真实事件形态

AtlasCore 已对真实 Dify streaming 做过联调，确认：

- 文本输入变量当前为 `query`
- 响应最前面可能出现裸 `event: ping`
- 业务事件很多只有 `data:` 行，事件名位于 JSON 的 `event` 字段
- 当前项目已兼容以下事件：`workflow_started`、`node_started`、`node_finished`、`text_chunk`、`workflow_finished`

其中对前端真正重要的只有：

- `workflow_started`
- `text_chunk`
- `workflow_finished`

AtlasCore 会把这些事件重新封装成对前端稳定的 SSE 事件：

- `start`
- `delta`
- `end`
- `error`

---

## 14. AtlasCore 侧推荐封装

建议在 AtlasCore 中建立一个专门的 Dify Client，至少封装以下方法：

```text
run_workflow(inputs, user, response_mode="blocking", trace_id=None)
run_workflow_by_id(workflow_id, inputs, user, response_mode="blocking", trace_id=None)
upload_file(file, user)
get_workflow_run(workflow_run_id)
stop_task(task_id, user)
get_parameters()
get_info()
get_logs(filters)
```

这样可以把：

- base url
- headers
- timeout
- 错误处理
- 重试策略
- 响应映射

全部集中管理。

---

## 15. AtlasCore 中建议配置的 Dify 参数

### 15.1 必配项

```text
DIFY_BASE_URL
DIFY_API_KEY
DIFY_TIMEOUT_SECONDS
```

### 15.2 强烈建议补充

```text
DIFY_WORKFLOW_ID
DIFY_RESPONSE_MODE
DIFY_TEXT_INPUT_VARIABLE
DIFY_FILE_INPUT_VARIABLE
DIFY_ENABLE_TRACE
DIFY_USER_PREFIX
```

### 15.3 推荐含义

#### `DIFY_BASE_URL`
Dify API 基础地址，通常为：

```text
https://api.dify.ai/v1
```

#### `DIFY_API_KEY`
后端使用的 Dify Service API Key。

#### `DIFY_TIMEOUT_SECONDS`
HTTP 调用超时时间。

#### `DIFY_WORKFLOW_ID`
指定版本 Workflow 的 ID。
如果为空，则默认走 `/workflows/run`。

#### `DIFY_RESPONSE_MODE`
`blocking` 或 `streaming`。

#### `DIFY_TEXT_INPUT_VARIABLE`
AtlasCore 传给 Dify 的文本变量名，例如 `query`。

#### `DIFY_FILE_INPUT_VARIABLE`
文件型变量名，例如 `orig_mail`。

#### `DIFY_ENABLE_TRACE`
是否启用 trace_id 透传。

#### `DIFY_USER_PREFIX`
用于给匿名用户拼接统一 user 标识。

### 15.4 Review Dify 独立配置

聊天 Dify 和评阅 Dify 在当前项目中已经分离配置，不应混用同一组变量。

建议最少配置：

```text
REVIEW_DIFY_BASE_URL
REVIEW_DIFY_API_KEY
REVIEW_DIFY_APP_MODE
REVIEW_DIFY_RESPONSE_MODE
REVIEW_DIFY_TEXT_INPUT_VARIABLE
REVIEW_DIFY_TIMEOUT
```

推荐补充：

```text
REVIEW_DIFY_WORKFLOW_ID
REVIEW_DIFY_FILE_INPUT_VARIABLE
REVIEW_DIFY_ENABLE_TRACE
REVIEW_DIFY_USER_PREFIX
```

推荐含义：

#### `REVIEW_DIFY_BASE_URL`
评阅 Dify API 基础地址。推荐填写：

```text
https://api.dify.ai
```

即不带 `/v1` 的基础地址。AtlasCore 运行时会兼容去重，但文档推荐使用规范值。

#### `REVIEW_DIFY_API_KEY`
评阅 Workflow 使用的独立 Service API Key，建议与聊天 Dify 分开。

#### `REVIEW_DIFY_APP_MODE`
当前评阅推荐使用 `workflow`。

#### `REVIEW_DIFY_RESPONSE_MODE`
当前评阅页推荐使用 `blocking`，由 AtlasCore 一次性返回结构化评阅结果。

#### `REVIEW_DIFY_TEXT_INPUT_VARIABLE`
评阅 Workflow 的真实文本输入变量名。当前项目推荐值为 `query`。

#### `REVIEW_DIFY_FILE_INPUT_VARIABLE`
仅在评阅 Workflow 确实有文件型输入时使用；当前纯文本评阅建议留空。

#### `REVIEW_DIFY_TIMEOUT`
评阅 Workflow 的超时秒数。评阅通常比聊天更慢，建议设置更高一些，例如 `300`。

#### `REVIEW_DIFY_USER_PREFIX`
用于给评阅链路拼接统一 Dify user 标识，默认 `review`。

---

## 16. 当前项目最小可用联调方案

为了尽快打通 AtlasCore 与 Dify，建议按下面的最小方案落地：

### 阶段一：最小可用

只接这 4 个接口：

1. `POST /workflows/run`
2. `POST /files/upload`
3. `GET /parameters`
4. `GET /workflows/run/{workflow_run_id}`

其中：

- 聊天走 `/workflows/run`
- 评阅也走 `/workflows/run`，但使用独立 Review Dify 配置
- 文档同步走 `/files/upload`
- 启动校验走 `/parameters`
- 排障与补查走 `/workflows/run/{workflow_run_id}`

### 16.1 评阅联调最小要求

若只验证评阅链路，至少要确认：

1. `REVIEW_DIFY_BASE_URL` 与 `REVIEW_DIFY_API_KEY` 已配置
2. `REVIEW_DIFY_TEXT_INPUT_VARIABLE` 与 Workflow 文本变量一致
3. `POST /review/evaluate` 返回的 `parse_status` 为 `success` 或 `partial`
4. 管理员可通过 `/api/admin/review/logs` 查看评阅日志与标准化结果

### 阶段二：体验增强

再增加：

5. `POST /workflows/tasks/{task_id}/stop`
6. `GET /workflows/logs`
7. `GET /info`
8. `POST /workflows/{workflow_id}/run`

---

## 17. 推荐联调顺序

### 第一步

先确认 Dify 应用已经可用：

- API Key 正确
- Workflow 已发布
- 输入变量名确认清楚
- 文件变量名确认清楚

### 第二步

AtlasCore 接入：

- `POST /workflows/run`
- `GET /parameters`

先让聊天主链路跑通。

### 第三步

接入 `POST /files/upload`，跑通管理员文档同步链路。

### 第四步

补上：

- `GET /workflows/run/{workflow_run_id}`
- `GET /workflows/logs`

增强诊断能力。

### 第五步

如有需要，再升级到：

- `streaming`
- `POST /workflows/tasks/{task_id}/stop`
- `POST /workflows/{workflow_id}/run`

---

## 18. 一句话结论

**对当前 AtlasCore 项目来说，Dify 最重要的接口不是一大堆，而是少数几个真正进入主链路的接口：`POST /workflows/run` 负责问答执行，`POST /files/upload` 负责文件输入，`GET /parameters` 负责输入定义校验，`GET /workflows/run/{workflow_run_id}` 负责状态补查；其余接口主要服务于流式增强、日志排查与版本稳定性。**
