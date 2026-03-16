"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { DataTableShell } from "@/components/common/data-table-shell";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { PageHeader } from "@/components/common/page-header";
import { ExportTable } from "@/components/admin/export-table";
import { Button } from "@/components/ui/button";
import { downloadExport, listExports, triggerLogExport } from "@/lib/api/exports";

export default function AdminExportsPage() {
  const queryClient = useQueryClient();
  const exportsQuery = useQuery({ queryKey: ["exports"], queryFn: listExports });
  const triggerMutation = useMutation({
    mutationFn: () => triggerLogExport("frontend-admin"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exports"] });
    }
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="导出管理"
        description="与现有 CSV 导出机制对齐。支持查看导出记录、触发问答日志导出，并点击即下载 CSV。"
        actions={
          <Button onClick={() => triggerMutation.mutate()} disabled={triggerMutation.isPending}>
            {triggerMutation.isPending ? "导出中..." : "导出问答日志"}
          </Button>
        }
      />
      {exportsQuery.isLoading ? <LoadingState label="正在加载导出记录..." /> : null}
      {exportsQuery.isError ? <ErrorState message={(exportsQuery.error as Error).message} /> : null}
      {!exportsQuery.isLoading && !exportsQuery.isError ? (
        <DataTableShell title="导出记录" description="若后端返回 `download_url`，前端会直接请求下载接口并触发浏览器下载。">
          {exportsQuery.data?.items.length ? (
            <ExportTable items={exportsQuery.data.items} onDownload={(item) => downloadExport(item.filename)} />
          ) : (
            <div className="p-5">
              <EmptyState title="暂无导出记录" description="点击上方按钮触发首次导出，完成后即可直接下载 CSV。" />
            </div>
          )}
        </DataTableShell>
      ) : null}
    </div>
  );
}
