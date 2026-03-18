"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { DataTableShell } from "@/components/common/data-table-shell";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { FilterBar } from "@/components/common/filter-bar";
import { LoadingState } from "@/components/common/loading-state";
import { PageHeader } from "@/components/common/page-header";
import { SearchInput } from "@/components/common/search-input";
import { LogTable } from "@/components/admin/log-table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { listAdminLogs } from "@/lib/api/logs";
import { formatDateTime } from "@/lib/utils";
import type { AdminLogRecord } from "@/types/api";

export default function AdminLogsPage() {
  const [selectedLog, setSelectedLog] = useState<AdminLogRecord | null>(null);
  const [keyword, setKeyword] = useState("");
  const [source, setSource] = useState("");
  const [liked, setLiked] = useState("");
  const [rating, setRating] = useState("");

  const query = useMemo(() => ({ keyword, source, liked, rating }), [keyword, liked, rating, source]);
  const logsQuery = useQuery({
    queryKey: ["admin-logs", query],
    queryFn: () => listAdminLogs(query)
  });

  return (
    <div className="space-y-6">
      <PageHeader title="问答日志与反馈" description="支持按关键词、来源、点赞和评分过滤，并为导出筛选模型预留同一套查询结构。" />
      <FilterBar>
        <SearchInput placeholder="搜索问题、答案或上下文" value={keyword} onChange={(event) => setKeyword(event.target.value)} />
        <Input placeholder="来源，如 atlascore" value={source} onChange={(event) => setSource(event.target.value)} />
        <Input placeholder="点赞状态 true / false" value={liked} onChange={(event) => setLiked(event.target.value)} />
        <Input placeholder="评分 1-5" value={rating} onChange={(event) => setRating(event.target.value)} />
        <div className="rounded-md border bg-panel px-3 py-2 text-sm text-muted-foreground">时间范围筛选可继续接入 URL 参数与日期控件。</div>
      </FilterBar>

      {logsQuery.isLoading ? <LoadingState label="正在加载日志..." /> : null}
      {logsQuery.isError ? <ErrorState message={(logsQuery.error as Error).message} /> : null}
      {!logsQuery.isLoading && !logsQuery.isError ? (
        <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
          <DataTableShell title="日志列表" description="默认展示最新问答记录和反馈摘要。">
            {logsQuery.data?.items.length ? (
              <LogTable items={logsQuery.data.items} onView={setSelectedLog} />
            ) : (
              <div className="p-5">
                <EmptyState title="没有匹配结果" description="调整筛选条件后重试，或等待新的问答记录写入。" />
              </div>
            )}
          </DataTableShell>

          <Card className="h-fit">
            <CardHeader>
              <CardTitle>日志详情</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              {selectedLog ? (
                <>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">问题</p>
                    <p className="mt-1 leading-7">{selectedLog.question}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-muted-foreground">答案</p>
                    <p className="mt-1 leading-7 text-muted-foreground">{selectedLog.answer}</p>
                  </div>
                  <div className="space-y-1 text-muted-foreground">
                    <p>姓名：{selectedLog.name_snapshot || "未记录"}</p>
                    <p>学号：{selectedLog.student_id_snapshot || "未记录"}</p>
                    <p>来源：{selectedLog.source}</p>
                    <p>时间：{formatDateTime(selectedLog.created_at)}</p>
                    <p>点赞：{selectedLog.feedback?.liked === null || selectedLog.feedback?.liked === undefined ? "未评价" : selectedLog.feedback.liked ? "是" : "否"}</p>
                    <p>评分：{selectedLog.feedback?.rating ?? "未评分"}</p>
                  </div>
                </>
              ) : (
                <p className="leading-6 text-muted-foreground">点击日志表格中的“查看”后，在这里展示问题、答案和反馈详情。当前采用右侧面板结构，后续可替换为抽屉。</p>
              )}
            </CardContent>
          </Card>
        </div>
      ) : null}
    </div>
  );
}
