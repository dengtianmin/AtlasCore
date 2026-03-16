"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { MessageSquareText, Network, ShieldCheck, HeartPulse, Download } from "lucide-react";

import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { PageHeader } from "@/components/common/page-header";
import { PublicHeader } from "@/components/common/public-header";
import { SummaryCard } from "@/components/admin/summary-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getCurrentAdmin } from "@/lib/api/admin-auth";
import { getLatestExport } from "@/lib/api/exports";
import { getHealth, getRootInfo } from "@/lib/api/system";
import { getAdminToken } from "@/lib/auth/token";
import { formatDateTime } from "@/lib/utils";

export default function HomePage() {
  const apiBaseUrl = process.env.NEXT_PUBLIC_ATLASCORE_API_BASE_URL || "http://127.0.0.1:8000";
  const token = getAdminToken();
  const rootQuery = useQuery({ queryKey: ["root"], queryFn: getRootInfo });
  const healthQuery = useQuery({ queryKey: ["health"], queryFn: getHealth });
  const meQuery = useQuery({
    queryKey: ["root-admin-me", token],
    queryFn: () => getCurrentAdmin(token),
    enabled: Boolean(token)
  });
  const latestExportQuery = useQuery({
    queryKey: ["root-latest-export", token],
    queryFn: getLatestExport,
    enabled: Boolean(token)
  });

  const isLoading = rootQuery.isLoading || healthQuery.isLoading;
  const errorMessage = (rootQuery.error as Error | undefined)?.message || (healthQuery.error as Error | undefined)?.message;

  return (
    <div>
      <PublicHeader />
      <main className="mx-auto max-w-7xl px-6 py-10">
        <PageHeader
          title="AtlasCore 轻量工作台"
          description="面向研究与知识系统的一体化桌面前端。普通用户可直接进入聊天与图谱浏览；管理员可进行文档、日志和导出管理。"
        />
        {isLoading ? <LoadingState label="正在加载系统状态..." /> : null}
        {!isLoading && errorMessage ? <ErrorState message={errorMessage} /> : null}
        {!isLoading && !errorMessage ? (
          <div className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <SummaryCard title="系统状态" value={healthQuery.data?.status ?? "unknown"} hint={healthQuery.data?.service} />
              <SummaryCard title="接口前缀" value={rootQuery.data?.exports_api.list ?? "/api/admin/exports"} hint="所有业务请求统一走 AtlasCore" />
              <SummaryCard title="管理员态" value={meQuery.data?.username ?? "未登录"} hint={meQuery.data ? "已验证管理身份" : "可从右上角进入登录"} />
              <SummaryCard
                title="最新导出"
                value={latestExportQuery.data?.filename ?? "暂无"}
                hint={latestExportQuery.data ? formatDateTime(latestExportQuery.data.export_time) : "登录管理员后可见"}
              />
            </div>

            <div className="grid gap-6 lg:grid-cols-[1.35fr_1fr]">
              <Card>
                <CardHeader>
                  <CardTitle>研究工具入口</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-4 md:grid-cols-3">
                  <Link href="/chat" className="rounded-lg border bg-panel p-4 transition-colors hover:bg-accent">
                    <MessageSquareText className="h-5 w-5 text-primary" />
                    <h3 className="mt-3 font-medium">进入聊天页</h3>
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">通过 AtlasCore 聊天接口提问、查看回答并记录反馈。</p>
                  </Link>
                  <Link href="/graph" className="rounded-lg border bg-panel p-4 transition-colors hover:bg-accent">
                    <Network className="h-5 w-5 text-primary" />
                    <h3 className="mt-3 font-medium">进入图谱页</h3>
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">浏览知识图谱、点击节点查看详情，并为后续高级交互预留结构。</p>
                  </Link>
                  <Link href={meQuery.data ? "/admin" : "/admin/login"} className="rounded-lg border bg-panel p-4 transition-colors hover:bg-accent">
                    <ShieldCheck className="h-5 w-5 text-primary" />
                    <h3 className="mt-3 font-medium">管理员入口</h3>
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">进行文档上传、问答日志筛选、CSV 导出与系统管理。</p>
                  </Link>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>系统说明</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 text-sm leading-7 text-muted-foreground">
                  <p>前端不直接连接 Dify 或外部图库。所有请求统一通过 AtlasCore API，由后端负责认证、文档管理、图谱查询、日志和导出。</p>
                  <p>当前版本优先桌面端体验，采用简约、学术、扁平化视觉系统，适合继续迭代为正式知识平台界面。</p>
                  <div className="flex flex-wrap gap-2">
                    <Link
                      href={`${apiBaseUrl}/health`}
                      target="_blank"
                      className="inline-flex h-10 items-center rounded-md border bg-card px-4 text-sm font-medium"
                    >
                      <HeartPulse className="mr-2 h-4 w-4" />
                      健康接口
                    </Link>
                    <Link href="/admin/exports" className="inline-flex h-10 items-center rounded-md border bg-card px-4 text-sm font-medium">
                      <Download className="mr-2 h-4 w-4" />
                      导出管理
                    </Link>
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>最近导出文件</CardTitle>
              </CardHeader>
              <CardContent>
                {latestExportQuery.data ? (
                  <div className="flex items-center justify-between gap-4 rounded-lg border bg-panel p-4">
                    <div>
                      <p className="font-medium">{latestExportQuery.data.filename}</p>
                      <p className="text-sm text-muted-foreground">
                        {latestExportQuery.data.record_count} 条记录 · {formatDateTime(latestExportQuery.data.export_time)}
                      </p>
                    </div>
                    <Link href="/admin/exports" className="inline-flex h-10 items-center rounded-md border bg-card px-4 text-sm font-medium">
                      查看导出页
                    </Link>
                  </div>
                ) : (
                  <EmptyState title="暂无导出记录" description="管理员登录后可以在后台触发问答日志导出，并在此查看最近结果。" />
                )}
              </CardContent>
            </Card>
          </div>
        ) : null}
      </main>
    </div>
  );
}
