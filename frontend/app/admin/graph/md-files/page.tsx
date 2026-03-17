"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { PageHeader } from "@/components/common/page-header";
import { StatusBadge } from "@/components/common/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TBody, TD, TH, THead } from "@/components/ui/table";
import { createExtractionTask, deleteMdFile, listMdFiles, uploadMdFile } from "@/lib/api/graph-extraction";
import { formatDateTime, formatFileSize } from "@/lib/utils";

export default function AdminMdFilesPage() {
  const queryClient = useQueryClient();
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const filesQuery = useQuery({ queryKey: ["graph-md-files"], queryFn: () => listMdFiles(100, 0) });
  const uploadMutation = useMutation({
    mutationFn: uploadMdFile,
    onSuccess: async (payload) => {
      setMessage(`已登记 Markdown 文件：${payload.filename}`);
      await queryClient.invalidateQueries({ queryKey: ["graph-md-files"] });
    }
  });
  const deleteMutation = useMutation({
    mutationFn: deleteMdFile,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["graph-md-files"] });
      setSelectedIds((current) => current.filter((id) => filesQuery.data?.items.some((item) => item.id !== id) ?? true));
    }
  });
  const taskMutation = useMutation({
    mutationFn: createExtractionTask,
    onSuccess: async (payload) => {
      setMessage(`抽取任务已完成，输出版本 ${payload.output_graph_version ?? "未标记"}`);
      setSelectedIds([]);
      await queryClient.invalidateQueries({ queryKey: ["graph-md-files"] });
      await queryClient.invalidateQueries({ queryKey: ["graph-extraction-tasks"] });
      await queryClient.invalidateQueries({ queryKey: ["admin-graph-status"] });
    }
  });

  const selectedCount = useMemo(() => selectedIds.length, [selectedIds]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Markdown 文件管理"
        description="上传后只做登记，不自动抽取。管理员可勾选多个 Markdown 文件，统一发起一次图谱抽取任务。"
        actions={
          <Button onClick={() => taskMutation.mutate(selectedIds)} disabled={!selectedCount || taskMutation.isPending}>
            {taskMutation.isPending ? "抽取中..." : `抽取所选文件 (${selectedCount})`}
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>上传 Markdown 文件</CardTitle>
        </CardHeader>
        <CardContent>
          <label className="flex max-w-md cursor-pointer items-center justify-between rounded-lg border border-dashed bg-panel px-4 py-4 text-sm">
            <span>选择 Markdown 文件并登记</span>
            <Input
              type="file"
              accept=".md,.markdown"
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

      {filesQuery.isLoading ? <LoadingState label="正在加载 Markdown 文件..." /> : null}
      {filesQuery.isError ? <ErrorState message={(filesQuery.error as Error).message} /> : null}
      {filesQuery.data ? (
        <Card>
          <CardHeader>
            <CardTitle>Markdown 文件列表</CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <Table>
              <THead>
                <tr>
                  <TH>选择</TH>
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
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(item.id)}
                        onChange={(event) => {
                          setSelectedIds((current) =>
                            event.target.checked ? [...current, item.id] : current.filter((value) => value !== item.id)
                          );
                        }}
                      />
                    </TD>
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
                      <Button variant="ghost" size="sm" onClick={() => deleteMutation.mutate(item.id)}>
                        删除
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
