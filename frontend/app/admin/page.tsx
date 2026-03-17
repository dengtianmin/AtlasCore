"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { DataTableShell } from "@/components/common/data-table-shell";
import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { PageHeader } from "@/components/common/page-header";
import { SummaryCard } from "@/components/admin/summary-card";
import { Card, CardContent } from "@/components/ui/card";
import { listDocuments } from "@/lib/api/documents";
import { listExports } from "@/lib/api/exports";
import { listAdminLogs } from "@/lib/api/logs";
import { getAdminSystemStatus } from "@/lib/api/system";
import { formatDateTime } from "@/lib/utils";

export default function AdminDashboardPage() {
  const healthQuery = useQuery({ queryKey: ["admin-system-status"], queryFn: getAdminSystemStatus });
  const documentsQuery = useQuery({ queryKey: ["admin-documents"], queryFn: () => listDocuments(10, 0) });
  const exportsQuery = useQuery({ queryKey: ["admin-exports"], queryFn: listExports });
  const logsQuery = useQuery({ queryKey: ["admin-logs-summary"], queryFn: () => listAdminLogs() });

  if (healthQuery.isLoading || documentsQuery.isLoading || exportsQuery.isLoading || logsQuery.isLoading) {
    return <LoadingState label="正在加载后台总览..." />;
  }

  const error = [healthQuery.error, documentsQuery.error, exportsQuery.error, logsQuery.error]
    .filter(Boolean)
    .map((item) => (item as Error).message)[0];
  if (error) {
    return <ErrorState message={error} />;
  }

  return (
    <div className="space-y-6">
      <PageHeader title="后台总览" description="面向 AtlasCore 管理员的轻量控制台，集中展示文档、导出、日志和系统状态。" />
      <div className="grid gap-4 xl:grid-cols-4">
        <SummaryCard title="文档数" value={documentsQuery.data?.items.length ?? 0} hint="当前页面拉取的最新文档样本" />
        <SummaryCard title="导出记录" value={exportsQuery.data?.items.length ?? 0} hint="CSV 导出历史" />
        <SummaryCard title="问答日志" value={logsQuery.data?.items.length ?? 0} hint="可进一步按条件筛选" />
        <SummaryCard
          title="系统状态"
          value={healthQuery.data?.app_ready ? "ready" : "not-ready"}
          hint={`${healthQuery.data?.app_env ?? "unknown"} / graph ${healthQuery.data?.graph_loaded ? "loaded" : "idle"}`}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_1fr]">
        <Card>
          <CardContent className="grid gap-4 p-5 md:grid-cols-2 xl:grid-cols-4">
            <Link href="/admin/documents" className="rounded-lg border bg-panel p-4 text-sm transition-colors hover:bg-accent">
              <p className="font-medium">文档管理</p>
              <p className="mt-2 leading-6 text-muted-foreground">上传、删除文档并触发同步。</p>
            </Link>
            <Link href="/admin/dify" className="rounded-lg border bg-panel p-4 text-sm transition-colors hover:bg-accent">
              <p className="font-medium">Dify 调试</p>
              <p className="mt-2 leading-6 text-muted-foreground">临时提交 Base URL 与 API Key，查看参数校验和调试日志。</p>
            </Link>
            <Link href="/admin/logs" className="rounded-lg border bg-panel p-4 text-sm transition-colors hover:bg-accent">
              <p className="font-medium">问答日志</p>
              <p className="mt-2 leading-6 text-muted-foreground">查看回答、反馈与筛选结果。</p>
            </Link>
            <Link href="/admin/exports" className="rounded-lg border bg-panel p-4 text-sm transition-colors hover:bg-accent">
              <p className="font-medium">导出管理</p>
              <p className="mt-2 leading-6 text-muted-foreground">触发 QA 日志导出并下载 CSV。</p>
            </Link>
          </CardContent>
        </Card>

        <DataTableShell
          title="最近导出记录"
          actions={
            <Link href="/admin/exports" className="inline-flex h-10 items-center rounded-md border bg-card px-4 text-sm font-medium">
              查看全部
            </Link>
          }
        >
          <div className="space-y-3 p-5">
            {exportsQuery.data?.items.slice(0, 3).map((item) => (
              <div key={item.export_id} className="rounded-lg border bg-panel p-4">
                <p className="font-medium">{item.filename}</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  {item.record_count} 条记录 · {formatDateTime(item.export_time)}
                </p>
              </div>
            ))}
          </div>
        </DataTableShell>
      </div>
    </div>
  );
}
