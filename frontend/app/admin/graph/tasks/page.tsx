"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { PageHeader } from "@/components/common/page-header";
import { StatusBadge } from "@/components/common/status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TBody, TD, TH, THead } from "@/components/ui/table";
import { getExtractionTask, listExtractionTasks } from "@/lib/api/graph-extraction";
import { formatDateTime } from "@/lib/utils";

function formatTaskProgress(completedChunks: number | null, totalChunks: number | null) {
  const completed = completedChunks ?? 0;
  const total = totalChunks ?? 0;
  return `${completed}/${total}`;
}

export default function AdminGraphTasksPage() {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const tasksQuery = useQuery({ queryKey: ["graph-extraction-tasks"], queryFn: () => listExtractionTasks(100, 0) });
  const detailQuery = useQuery({
    queryKey: ["graph-extraction-task-detail", selectedTaskId],
    queryFn: () => getExtractionTask(selectedTaskId!),
    enabled: Boolean(selectedTaskId)
  });

  return (
    <div className="space-y-6">
      <PageHeader title="图谱抽取任务" description="查看最近任务、失败原因、输出图版本和所选文档集合。" />

      {tasksQuery.isLoading ? <LoadingState label="正在加载抽取任务..." /> : null}
      {tasksQuery.isError ? <ErrorState message={(tasksQuery.error as Error).message} /> : null}

      {tasksQuery.data ? (
        <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
          <Card>
            <CardHeader>
              <CardTitle>任务列表</CardTitle>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <Table>
                <THead>
                  <tr>
                    <TH>ID</TH>
                    <TH>状态</TH>
                    <TH>进度</TH>
                    <TH>开始时间</TH>
                    <TH>输出版本</TH>
                  </tr>
                </THead>
                <TBody>
                  {tasksQuery.data.items.map((item) => (
                    <tr key={item.id} className="cursor-pointer" onClick={() => setSelectedTaskId(item.id)}>
                      <TD>{item.id.slice(0, 8)}</TD>
                      <TD><StatusBadge value={item.status} /></TD>
                      <TD>{formatTaskProgress(item.graph_extraction_completed_chunks, item.graph_extraction_chunk_count)}</TD>
                      <TD>{formatDateTime(item.started_at ?? item.created_at)}</TD>
                      <TD>{item.output_graph_version ?? "无"}</TD>
                    </tr>
                  ))}
                </TBody>
              </Table>
            </CardContent>
          </Card>

          <Card className="h-fit">
            <CardHeader>
              <CardTitle>任务详情</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {detailQuery.isLoading ? <LoadingState label="正在加载任务详情..." /> : null}
              {detailQuery.data ? (
                <>
                  <p>任务类型：{detailQuery.data.task_type ?? "未知"}</p>
                  <p>状态：{detailQuery.data.status}</p>
                  <p>操作人：{detailQuery.data.operator ?? "未知"}</p>
                  <p>进度：{formatTaskProgress(detailQuery.data.graph_extraction_completed_chunks, detailQuery.data.graph_extraction_chunk_count)}</p>
                  <p>开始时间：{formatDateTime(detailQuery.data.started_at ?? detailQuery.data.created_at)}</p>
                  <p>结束时间：{formatDateTime(detailQuery.data.finished_at)}</p>
                  <p>输出版本：{detailQuery.data.output_graph_version ?? "无"}</p>
                  <p>所选文档：{detailQuery.data.selected_document_ids?.join(", ") ?? "无"}</p>
                  {detailQuery.data.result_summary ? <p>结果摘要：{detailQuery.data.result_summary}</p> : null}
                  {detailQuery.data.error_message ? <p className="text-destructive">失败原因：{detailQuery.data.error_message}</p> : null}
                </>
              ) : (
                <p className="text-muted-foreground">点击左侧任务查看详情。</p>
              )}
            </CardContent>
          </Card>
        </div>
      ) : null}
    </div>
  );
}
