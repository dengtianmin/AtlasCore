"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { DataTableShell } from "@/components/common/data-table-shell";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { PageHeader } from "@/components/common/page-header";
import { DocumentTable } from "@/components/admin/document-table";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { deleteDocument, getDocument, listDocuments, syncDocumentToDify, syncDocumentToGraph, uploadDocument } from "@/lib/api/documents";
import { formatDateTime, formatFileSize } from "@/lib/utils";
import type { DocumentRecord } from "@/types/api";
import { ApiError } from "@/lib/api/client";

function toErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    return error.detail;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "请求失败";
}

export default function AdminDocumentsPage() {
  const queryClient = useQueryClient();
  const [selectedDocument, setSelectedDocument] = useState<DocumentRecord | null>(null);
  const documentsQuery = useQuery({ queryKey: ["documents"], queryFn: () => listDocuments(100, 0) });
  const detailQuery = useQuery({
    queryKey: ["document-detail", selectedDocument?.id],
    queryFn: () => getDocument(selectedDocument!.id),
    enabled: Boolean(selectedDocument?.id)
  });

  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ["documents"] });
    if (selectedDocument?.id) {
      await queryClient.invalidateQueries({ queryKey: ["document-detail", selectedDocument.id] });
    }
  };
  const uploadMutation = useMutation({
    mutationFn: uploadDocument,
    onSuccess: (document) => {
      void invalidate();
      setSelectedDocument(document);
    }
  });
  const deleteMutation = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      void invalidate();
      setSelectedDocument(null);
    }
  });
  const syncGraphMutation = useMutation({
    mutationFn: syncDocumentToGraph,
    onSuccess: () => void invalidate()
  });
  const syncDifyMutation = useMutation({
    mutationFn: syncDocumentToDify,
    onSuccess: () => void invalidate()
  });

  return (
    <div className="space-y-6">
      <PageHeader title="文档管理" description="统一展示文档列表、上传入口、详情查看与图谱/Dify 同步动作。" />

      <Card>
        <CardHeader>
          <CardTitle>上传文档</CardTitle>
        </CardHeader>
        <CardContent>
          <label className="flex max-w-md cursor-pointer items-center justify-between rounded-lg border border-dashed bg-panel px-4 py-4 text-sm">
            <span>选择文件并上传到 AtlasCore</span>
            <Input
              type="file"
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
          {uploadMutation.isError ? <p className="mt-3 text-sm text-destructive">{toErrorMessage(uploadMutation.error)}</p> : null}
        </CardContent>
      </Card>

      {documentsQuery.isLoading ? <LoadingState label="正在加载文档..." /> : null}
      {documentsQuery.isError ? <ErrorState message={(documentsQuery.error as Error).message} /> : null}
      {!documentsQuery.isLoading && !documentsQuery.isError ? (
        <div className="grid gap-6 xl:grid-cols-[1fr_340px]">
          <DataTableShell title="文档列表" description="支持删除、查看详情，以及同步到图谱或 Dify。">
            {documentsQuery.data?.items.length ? (
              <DocumentTable
                items={documentsQuery.data.items}
                onView={setSelectedDocument}
                onDelete={(item) => deleteMutation.mutate(item.id)}
                onSyncGraph={(item) => syncGraphMutation.mutate(item.id)}
                onSyncDify={(item) => syncDifyMutation.mutate(item.id)}
              />
            ) : (
              <div className="p-5">
                <EmptyState title="暂无文档" description="上传第一个文件后，这里会展示文档状态、同步信息和详情入口。" />
              </div>
            )}
          </DataTableShell>

          <Card className="h-fit">
            <CardHeader>
              <CardTitle>文档详情</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {detailQuery.data ? (
                <>
                  <div>
                    <p className="font-medium">{detailQuery.data.filename}</p>
                    <p className="text-muted-foreground">{detailQuery.data.mime_type ?? detailQuery.data.content_type ?? detailQuery.data.source_type}</p>
                  </div>
                  <div className="space-y-1 leading-6 text-muted-foreground">
                    <p>状态：{detailQuery.data.status}</p>
                    <p>Dify 同步状态：{detailQuery.data.dify_sync_status ?? "未记录"}</p>
                    <p>上传时间：{formatDateTime(detailQuery.data.uploaded_at)}</p>
                    <p>大小：{formatFileSize(detailQuery.data.file_size)}</p>
                    <p>MIME：{detailQuery.data.mime_type ?? "未知"}</p>
                    <p>扩展名：{detailQuery.data.file_extension ?? "未知"}</p>
                    <p>图谱同步：{detailQuery.data.synced_to_graph ? "已同步" : "未同步"}</p>
                    <p>Dify 同步：{detailQuery.data.synced_to_dify ? "已同步" : "未同步"}</p>
                    <p>Dify File ID：{detailQuery.data.dify_upload_file_id ?? "无"}</p>
                    <p>Dify 上传时间：{detailQuery.data.dify_uploaded_at ? formatDateTime(detailQuery.data.dify_uploaded_at) : "无"}</p>
                    <p>最近同步目标：{detailQuery.data.last_sync_target ?? "无"}</p>
                    <p>最近同步状态：{detailQuery.data.last_sync_status ?? "无"}</p>
                    <p>最近同步时间：{detailQuery.data.last_sync_at ? formatDateTime(detailQuery.data.last_sync_at) : "无"}</p>
                    <p>文件输入变量：{detailQuery.data.dify_file_input_variable ?? "未配置"}</p>
                  </div>
                  {detailQuery.data.note ? <p className="rounded-md bg-muted px-3 py-2 text-xs leading-5">备注：{detailQuery.data.note}</p> : null}
                  {detailQuery.data.dify_error_message ? (
                    <p className="rounded-md border border-destructive/20 bg-destructive/5 px-3 py-2 text-xs leading-5 text-destructive">
                      Dify 错误：{detailQuery.data.dify_error_code ? `${detailQuery.data.dify_error_code} - ` : ""}
                      {detailQuery.data.dify_error_message}
                    </p>
                  ) : null}
                  {detailQuery.data.dify_workflow_file_input ? (
                    <div className="rounded-md bg-muted px-3 py-2 text-xs leading-5">
                      <p className="mb-2 font-medium text-foreground">Workflow 文件输入预览</p>
                      <pre className="overflow-x-auto whitespace-pre-wrap">
                        {JSON.stringify(detailQuery.data.dify_workflow_file_input, null, 2)}
                      </pre>
                    </div>
                  ) : null}
                </>
              ) : (
                <p className="leading-6 text-muted-foreground">点击表格中的“详情”后，在这里查看文件详情。第一版使用右侧面板形式，后续可替换为抽屉。</p>
              )}
            </CardContent>
          </Card>
        </div>
      ) : null}

      {deleteMutation.isError ? <p className="text-sm text-destructive">删除失败：{toErrorMessage(deleteMutation.error)}</p> : null}
      {syncGraphMutation.isError ? <p className="text-sm text-destructive">图谱同步失败：{toErrorMessage(syncGraphMutation.error)}</p> : null}
      {syncDifyMutation.isError ? <p className="text-sm text-destructive">Dify 同步失败：{toErrorMessage(syncDifyMutation.error)}</p> : null}
    </div>
  );
}
