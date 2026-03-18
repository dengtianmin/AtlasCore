"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { DataTableShell } from "@/components/common/data-table-shell";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TBody, TD, TH, THead } from "@/components/ui/table";
import { listReviewLogs } from "@/lib/api/review";
import { formatDateTime } from "@/lib/utils";
import type { ReviewLogRecord } from "@/types/api";

export default function AdminReviewLogsPage() {
  const [selected, setSelected] = useState<ReviewLogRecord | null>(null);
  const logsQuery = useQuery({
    queryKey: ["admin-review-logs"],
    queryFn: listReviewLogs
  });

  return (
    <div className="space-y-6">
      <PageHeader title="评阅日志" description="查看用户评阅记录、姓名学号快照、评分风险等级以及原始回包和标准化结果。" />

      {logsQuery.isLoading ? <LoadingState label="正在加载评阅日志..." /> : null}
      {logsQuery.isError ? <ErrorState message={(logsQuery.error as Error).message} /> : null}
      {!logsQuery.isLoading && !logsQuery.isError ? (
        <div className="grid gap-6 xl:grid-cols-[1fr_380px]">
          <DataTableShell title="评阅记录" description="记录与普通用户身份快照绑定。点击“查看”可在右侧查看原始响应和标准化结果。">
            {logsQuery.data?.items.length ? (
              <div className="overflow-x-auto">
                <Table>
                  <THead>
                    <tr>
                      <TH>学生</TH>
                      <TH>输入</TH>
                      <TH>结果</TH>
                      <TH>时间</TH>
                      <TH>操作</TH>
                    </tr>
                  </THead>
                  <TBody>
                    {logsQuery.data.items.map((item) => (
                      <tr key={item.id}>
                        <TD>
                          <div className="space-y-1 text-xs">
                            <p className="font-medium">{item.name_snapshot || "未记录"}</p>
                            <p className="text-muted-foreground">{item.student_id_snapshot || "未记录"}</p>
                          </div>
                        </TD>
                        <TD>
                          <div className="max-w-xl">
                            <p className="line-clamp-2 text-sm text-slate-900">{item.review_input}</p>
                          </div>
                        </TD>
                        <TD>
                          <div className="space-y-1 text-xs">
                            <p>分数：{item.score ?? "未生成"}</p>
                            <p>风险：{item.risk_level ?? "未生成"}</p>
                            <p>解析：{item.parse_status}</p>
                          </div>
                        </TD>
                        <TD>{formatDateTime(item.created_at)}</TD>
                        <TD>
                          <Button variant="ghost" size="sm" onClick={() => setSelected(item)}>
                            查看
                          </Button>
                        </TD>
                      </tr>
                    ))}
                  </TBody>
                </Table>
              </div>
            ) : (
              <div className="p-5">
                <EmptyState title="暂无评阅日志" description="用户完成首次评阅后，这里会显示日志记录。" />
              </div>
            )}
          </DataTableShell>

          <Card className="h-fit">
            <CardHeader>
              <CardTitle>日志详情</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              {selected ? (
                <>
                  <div className="space-y-1 text-muted-foreground">
                    <p>姓名：{selected.name_snapshot || "未记录"}</p>
                    <p>学号：{selected.student_id_snapshot || "未记录"}</p>
                    <p>评分：{selected.score ?? "未生成"}</p>
                    <p>风险等级：{selected.risk_level ?? "未生成"}</p>
                    <p>解析状态：{selected.parse_status}</p>
                  </div>
                  <div>
                    <p className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">评阅输入</p>
                    <p className="leading-6">{selected.review_input}</p>
                  </div>
                  <div>
                    <p className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">原始响应</p>
                    <pre className="overflow-x-auto rounded-lg bg-slate-950 p-4 text-xs text-slate-100">{selected.raw_response || "无"}</pre>
                  </div>
                  <div>
                    <p className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">标准化结果</p>
                    <pre className="overflow-x-auto rounded-lg bg-slate-950 p-4 text-xs text-slate-100">{selected.normalized_result || "无"}</pre>
                  </div>
                </>
              ) : (
                <p className="leading-6 text-muted-foreground">点击左侧“查看”后，在这里显示原始响应和标准化结果。</p>
              )}
            </CardContent>
          </Card>
        </div>
      ) : null}
    </div>
  );
}
