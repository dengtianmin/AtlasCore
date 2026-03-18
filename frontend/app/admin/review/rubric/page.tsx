"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getReviewDifyConfig, getReviewRubric, updateReviewDifyConfig } from "@/lib/api/review";
import { formatDateTime } from "@/lib/utils";

export default function AdminReviewRubricPage() {
  const queryClient = useQueryClient();
  const rubricQuery = useQuery({
    queryKey: ["review-rubric"],
    queryFn: getReviewRubric
  });
  const configQuery = useQuery({
    queryKey: ["review-dify-config"],
    queryFn: getReviewDifyConfig
  });

  const [configForm, setConfigForm] = useState({
    base_url: "",
    api_key: "",
    app_mode: "workflow" as "workflow" | "chat",
    response_mode: "blocking" as "blocking" | "streaming",
    timeout_seconds: 30,
    workflow_id: "",
    text_input_variable: "",
    file_input_variable: "",
    enable_trace: false,
    user_prefix: "review"
  });

  const configMutation = useMutation({
    mutationFn: updateReviewDifyConfig,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["review-dify-config"] });
      setConfigForm((current) => ({ ...current, api_key: "" }));
    }
  });

  useEffect(() => {
    if (configQuery.data) {
      setConfigForm({
        base_url: configQuery.data.base_url ?? "",
        api_key: "",
        app_mode: configQuery.data.app_mode,
        response_mode: configQuery.data.response_mode,
        timeout_seconds: configQuery.data.timeout_seconds,
        workflow_id: "",
        text_input_variable: configQuery.data.text_input_variable ?? "",
        file_input_variable: configQuery.data.file_input_variable ?? "",
        enable_trace: configQuery.data.enable_trace,
        user_prefix: configQuery.data.user_prefix
      });
    }
  }, [configQuery.data]);

  const submitConfig = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    configMutation.mutate({
      ...configForm,
      base_url: configForm.base_url.trim() || null,
      api_key: configForm.api_key.trim() || null,
      workflow_id: configForm.workflow_id.trim() || null,
      text_input_variable: configForm.text_input_variable.trim() || null,
      file_input_variable: configForm.file_input_variable.trim() || null
    });
  };

  if (rubricQuery.isLoading || configQuery.isLoading) {
    return <LoadingState label="正在加载评阅配置..." />;
  }
  if (rubricQuery.isError) {
    return <ErrorState message={(rubricQuery.error as Error).message} />;
  }
  if (configQuery.isError) {
    return <ErrorState message={(configQuery.error as Error).message} />;
  }

  const rubric = rubricQuery.data ?? {
    rubric_text: "",
    updated_at: null,
    updated_by: null,
    is_active: false
  };
  const config = configQuery.data;

  return (
    <div className="space-y-6">
      <PageHeader
        title="评阅配置"
        description="这里管理评阅 Dify 运行参数。若服务端已经用环境变量注入，页面中的 Base URL 和 API Key 也可以作为后台覆盖配置使用。"
        actions={
          <Link
            href="/admin/review/logs"
            className="inline-flex h-10 items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            查看评阅日志
          </Link>
        }
      />

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>当前评分标准</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p>当前状态：{rubric.is_active ? "已生效" : "未配置"}</p>
            <p>最近更新时间：{formatDateTime(rubric.updated_at)}</p>
            <p>最近更新人：{rubric.updated_by ?? "未记录"}</p>
            <p>评分标准编辑已从当前页面移除。</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>评阅 Dify 摘要</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p>启用状态：{config?.enabled ? "已启用" : "未启用"}</p>
            <p>模式：{config?.app_mode}</p>
            <p>响应模式：{config?.response_mode}</p>
            <p>超时：{config?.timeout_seconds} 秒</p>
            <p>Base URL：{config?.base_url ?? "未配置"}</p>
            <p>API Key：{config?.has_api_key ? "已配置" : "未配置"}</p>
            <p>Workflow ID：{config?.workflow_id_configured ? "已配置" : "未配置"}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>评阅 Dify 运行参数</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={submitConfig}>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2 md:col-span-2">
                <label className="text-sm font-medium">REVIEW_DIFY_BASE_URL</label>
                <Input
                  placeholder="https://api.dify.ai"
                  value={configForm.base_url}
                  onChange={(event) => setConfigForm((current) => ({ ...current, base_url: event.target.value }))}
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <label className="text-sm font-medium">REVIEW_DIFY_API_KEY</label>
                <Input
                  type="password"
                  placeholder={config?.has_api_key ? "已配置，留空则保持不变" : "app-..."}
                  value={configForm.api_key}
                  onChange={(event) => setConfigForm((current) => ({ ...current, api_key: event.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">模式</label>
                <select
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  value={configForm.app_mode}
                  onChange={(event) => setConfigForm((current) => ({ ...current, app_mode: event.target.value as "workflow" | "chat" }))}
                >
                  <option value="workflow">workflow</option>
                  <option value="chat">chat</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">响应模式</label>
                <select
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  value={configForm.response_mode}
                  onChange={(event) =>
                    setConfigForm((current) => ({ ...current, response_mode: event.target.value as "blocking" | "streaming" }))
                  }
                >
                  <option value="blocking">blocking</option>
                  <option value="streaming">streaming</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">超时</label>
                <Input
                  type="number"
                  min={1}
                  max={300}
                  value={configForm.timeout_seconds}
                  onChange={(event) => setConfigForm((current) => ({ ...current, timeout_seconds: Number(event.target.value || 30) }))}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Workflow ID</label>
                <Input
                  value={configForm.workflow_id}
                  onChange={(event) => setConfigForm((current) => ({ ...current, workflow_id: event.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">文本变量名</label>
                <Input
                  placeholder="REVIEW_DIFY_TEXT_INPUT_VARIABLE"
                  value={configForm.text_input_variable}
                  onChange={(event) => setConfigForm((current) => ({ ...current, text_input_variable: event.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">文件变量名</label>
                <Input
                  placeholder="REVIEW_DIFY_FILE_INPUT_VARIABLE"
                  value={configForm.file_input_variable}
                  onChange={(event) => setConfigForm((current) => ({ ...current, file_input_variable: event.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">用户前缀</label>
                <Input
                  value={configForm.user_prefix}
                  onChange={(event) => setConfigForm((current) => ({ ...current, user_prefix: event.target.value }))}
                />
              </div>
              <label className="flex items-center gap-2 rounded-md border px-3 py-2 text-sm">
                <input
                  type="checkbox"
                  checked={configForm.enable_trace}
                  onChange={(event) => setConfigForm((current) => ({ ...current, enable_trace: event.target.checked }))}
                />
                启用 trace
              </label>
            </div>
            {configMutation.isError ? <ErrorState message={(configMutation.error as Error).message} /> : null}
            <Button type="submit" disabled={configMutation.isPending}>
              {configMutation.isPending ? "保存中..." : "保存评阅 Dify 配置"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
