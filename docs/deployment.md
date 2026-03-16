# AtlasCore Runtime Notes

## Azure App Service 最少检查项

- 确认容器通过 `PORT` 监听。
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

## 运行状态接口

- `/health`：始终返回 `{"status":"ok"}`。
- `/health/ready`：返回安全摘要，不包含 secret 明文。
