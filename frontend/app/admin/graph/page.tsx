"use client";

import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { SummaryCard } from "@/components/admin/summary-card";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { PageHeader } from "@/components/common/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { downloadGraphExport, exportGraph, getGraphAdminStatus, importGraph, reloadGraph } from "@/lib/api/graph-admin";

function formatDateTime(value: string | null) {
  if (!value) {
    return "未加载";
  }
  return new Date(value).toLocaleString("zh-CN");
}

export default function AdminGraphPage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string>("");

  const statusQuery = useQuery({
    queryKey: ["admin-graph-status"],
    queryFn: getGraphAdminStatus
  });

  const reloadMutation = useMutation({
    mutationFn: reloadGraph,
    onSuccess: (payload) => {
      setMessage(`图已重载：${payload.node_count} 个节点，${payload.edge_count} 条边。`);
      queryClient.invalidateQueries({ queryKey: ["admin-graph-status"] });
    }
  });

  const exportMutation = useMutation({
    mutationFn: exportGraph,
    onSuccess: async (payload) => {
      setMessage(`图快照已导出：${payload.filename}`);
      queryClient.invalidateQueries({ queryKey: ["admin-graph-status"] });
      await downloadGraphExport(payload.filename);
    }
  });

  const importMutation = useMutation({
    mutationFn: importGraph,
    onSuccess: (payload) => {
      setMessage(`图快照已导入：${payload.filename}，当前版本 ${payload.current_version ?? "未标记"}`);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      queryClient.invalidateQueries({ queryKey: ["admin-graph-status"] });
    }
  });

  const status = statusQuery.data;

  return (
    <div className="space-y-6">
      <PageHeader
        title="图管理"
        description="面向管理员的轻量图控制台。支持查看当前图状态、导出 SQLite 快照、导入新图文件并触发运行时重载。"
        actions={
          <>
            <Button variant="secondary" onClick={() => statusQuery.refetch()} disabled={statusQuery.isFetching}>
              {statusQuery.isFetching ? "刷新中..." : "刷新状态"}
            </Button>
            <Button onClick={() => reloadMutation.mutate()} disabled={reloadMutation.isPending}>
              {reloadMutation.isPending ? "重载中..." : "重载图"}
            </Button>
          </>
        }
      />

      {statusQuery.isLoading ? <LoadingState label="正在加载图状态..." /> : null}
      {statusQuery.isError ? <ErrorState message={(statusQuery.error as Error).message} /> : null}

      {!statusQuery.isLoading && !statusQuery.isError && status ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <SummaryCard title="模块状态" value={status.enabled ? "已启用" : "已禁用"} hint={status.loaded ? "运行时图已加载" : "运行时图未加载"} />
            <SummaryCard title="节点数" value={status.node_count} hint={`当前版本：${status.current_version ?? "未标记"}`} />
            <SummaryCard title="边数" value={status.edge_count} hint={`最近加载：${formatDateTime(status.last_loaded_at)}`} />
            <SummaryCard title="实例图文件" value={status.instance_local_path.split("/").pop() ?? "graph.db"} hint={status.instance_local_path} />
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>图状态详情</CardTitle>
                  <p className="mt-1 text-sm text-muted-foreground">这里显示当前实例图文件、导入导出目录与运行状态，便于排查本地图库是否已经正确切换。</p>
                </div>
                <Badge variant={status.loaded ? "success" : "warning"}>{status.loaded ? "Loaded" : "Not Loaded"}</Badge>
              </CardHeader>
              <CardContent className="space-y-4 text-sm">
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="rounded-lg border bg-muted/40 p-4">
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">SQLite 路径</p>
                    <p className="mt-2 break-all font-medium">{status.sqlite_path}</p>
                  </div>
                  <div className="rounded-lg border bg-muted/40 p-4">
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">实例图库</p>
                    <p className="mt-2 break-all font-medium">{status.instance_local_path}</p>
                    <p className="mt-1 text-xs text-muted-foreground">{status.instance_local_path_exists ? "实例本地图存在" : "实例本地图不存在"}</p>
                  </div>
                  <div className="rounded-lg border bg-muted/40 p-4">
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">导入目录</p>
                    <p className="mt-2 break-all font-medium">{status.import_dir}</p>
                    <p className="mt-1 text-xs text-muted-foreground">{status.import_dir_exists ? "目录可用" : "目录不存在"}</p>
                  </div>
                  <div className="rounded-lg border bg-muted/40 p-4">
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">导出目录</p>
                    <p className="mt-2 break-all font-medium">{status.export_dir}</p>
                    <p className="mt-1 text-xs text-muted-foreground">{status.export_dir_exists ? "目录可用" : "目录不存在"}</p>
                  </div>
                </div>
                <div className="rounded-lg border bg-muted/40 p-4">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">多实例规则</p>
                  <p className="mt-2 font-medium">{status.multi_instance_mode}</p>
                  <p className="mt-1 text-xs text-muted-foreground">每个实例只允许使用自己的本地 SQLite 图文件，不共享在线写库。</p>
                </div>
                {message ? <div className="rounded-lg border border-primary/20 bg-accent/50 px-4 py-3 text-sm">{message}</div> : null}
              </CardContent>
            </Card>

            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <div>
                    <CardTitle>导出当前图</CardTitle>
                    <p className="mt-1 text-sm text-muted-foreground">后端会把当前实例图 SQLite 复制为快照文件，并返回可下载文件名。</p>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Button className="w-full" onClick={() => exportMutation.mutate()} disabled={exportMutation.isPending}>
                    {exportMutation.isPending ? "正在导出..." : "导出并下载 SQLite"}
                  </Button>
                  <p className="text-xs leading-5 text-muted-foreground">适合在切换图数据前先留一个本地快照，便于快速回滚和比对。</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <div>
                    <CardTitle>导入新图</CardTitle>
                    <p className="mt-1 text-sm text-muted-foreground">上传一个包含 `graph_nodes`、`graph_edges`、`graph_sync_records`、`graph_versions` 的 SQLite 文件。</p>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Input
                    ref={fileInputRef}
                    type="file"
                    accept=".db,.sqlite,.sqlite3"
                    onChange={(event) => {
                      const file = event.target.files?.[0] ?? null;
                      setSelectedFile(file);
                    }}
                  />
                  {selectedFile ? (
                    <div className="rounded-lg border bg-muted/40 px-4 py-3 text-sm">
                      <p className="font-medium">{selectedFile.name}</p>
                      <p className="mt-1 text-muted-foreground">{Math.max(1, Math.round(selectedFile.size / 1024))} KB</p>
                    </div>
                  ) : (
                    <EmptyState title="尚未选择文件" description="先选择一个 SQLite 快照，再执行导入。" />
                  )}
                  <Button
                    className="w-full"
                    disabled={!selectedFile || importMutation.isPending}
                    onClick={() => {
                      if (selectedFile) {
                        importMutation.mutate(selectedFile);
                      }
                    }}
                  >
                    {importMutation.isPending ? "正在导入..." : "导入并重载图"}
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
