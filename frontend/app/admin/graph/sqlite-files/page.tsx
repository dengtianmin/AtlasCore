"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { PageHeader } from "@/components/common/page-header";
import { StatusBadge } from "@/components/common/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TBody, TD, TH, THead } from "@/components/ui/table";
import { activateSqliteFile, listSqliteFiles, uploadSqliteFile } from "@/lib/api/graph-extraction";
import { formatDateTime, formatFileSize } from "@/lib/utils";

export default function AdminSqliteFilesPage() {
  const queryClient = useQueryClient();
  const [message, setMessage] = useState("");
  const filesQuery = useQuery({ queryKey: ["graph-sqlite-files"], queryFn: () => listSqliteFiles(100, 0) });
  const uploadMutation = useMutation({
    mutationFn: uploadSqliteFile,
    onSuccess: async (payload) => {
      setMessage(`已上传 SQLite 文件：${payload.filename}`);
      await queryClient.invalidateQueries({ queryKey: ["graph-sqlite-files"] });
    }
  });
  const activateMutation = useMutation({
    mutationFn: activateSqliteFile,
    onSuccess: async (payload) => {
      setMessage(`已切换当前图谱版本：${payload.current_version ?? "未标记"}`);
      await queryClient.invalidateQueries({ queryKey: ["graph-sqlite-files"] });
      await queryClient.invalidateQueries({ queryKey: ["admin-graph-status"] });
    }
  });

  return (
    <div className="space-y-6">
      <PageHeader title="SQLite 文件管理" description="用于图谱整库替换、版本切换、恢复与初始化。上传后登记为快照文件，再手动切换当前线上图谱。" />

      <Card>
        <CardHeader>
          <CardTitle>上传 SQLite 快照</CardTitle>
        </CardHeader>
        <CardContent>
          <label className="flex max-w-md cursor-pointer items-center justify-between rounded-lg border border-dashed bg-panel px-4 py-4 text-sm">
            <span>选择 SQLite 文件并登记</span>
            <Input
              type="file"
              accept=".db,.sqlite,.sqlite3"
              className="hidden"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) {
                  uploadMutation.mutate(file);
                }
              }}
            />
            <span className="rounded-md border bg-white px-3 py-2">选择文件</span>
          </label>
          {message ? <p className="mt-3 text-sm text-muted-foreground">{message}</p> : null}
        </CardContent>
      </Card>

      {filesQuery.isLoading ? <LoadingState label="正在加载 SQLite 文件..." /> : null}
      {filesQuery.isError ? <ErrorState message={(filesQuery.error as Error).message} /> : null}

      {filesQuery.data ? (
        <Card>
          <CardHeader>
            <CardTitle>SQLite 文件列表</CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <Table>
              <THead>
                <tr>
                  <TH>文件</TH>
                  <TH>状态</TH>
                  <TH>上传时间</TH>
                  <TH>大小</TH>
                  <TH>操作</TH>
                </tr>
              </THead>
              <TBody>
                {filesQuery.data.items.map((item) => (
                  <tr key={item.id}>
                    <TD>
                      <div>
                        <p className="font-medium">{item.filename}</p>
                        <p className="text-xs text-muted-foreground">{item.note ?? item.local_path}</p>
                      </div>
                    </TD>
                    <TD><StatusBadge value={item.status} /></TD>
                    <TD>{formatDateTime(item.uploaded_at)}</TD>
                    <TD>{formatFileSize(item.file_size)}</TD>
                    <TD>
                      <Button size="sm" onClick={() => activateMutation.mutate(item.id)} disabled={activateMutation.isPending}>
                        切换为当前版本
                      </Button>
                    </TD>
                  </tr>
                ))}
              </TBody>
            </Table>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
