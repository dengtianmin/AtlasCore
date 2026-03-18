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
import { Textarea } from "@/components/ui/textarea";
import { getReviewDifyConfig, getReviewRubric, updateReviewDifyConfig, updateReviewRubric } from "@/lib/api/review";
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

  const [draft, setDraft] = useState("");
  const [configForm, setConfigForm] = useState({
    app_mode: "workflow" as "workflow" | "chat",
    response_mode: "blocking" as "blocking" | "streaming",
    timeout_seconds: 30,
    workflow_id: "",
    text_input_variable: "",
    file_input_variable: "",
    enable_trace: false,
    user_prefix: "review"
  });

  const updateMutation = useMutation({
    mutationFn: updateReviewRubric,
    onSuccess: async (payload) => {
      setDraft(payload.rubric_text);
      await queryClient.invalidateQueries({ queryKey: ["review-rubric"] });
    }
  });

  const configMutation = useMutation({
    mutationFn: updateReviewDifyConfig,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["review-dify-config"] });
    }
  });

  useEffect(() => {
    if (rubricQuery.data) {
      setDraft(rubricQuery.data.rubric_text);
    }
  }, [rubricQuery.data]);

  useEffect(() => {
    if (configQuery.data) {
      setConfigForm({
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

  const submitRubric = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    updateMutation.mutate(draft.trim());
  };

  const submitConfig = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    configMutation.mutate({
      ...configForm,
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
        description="这里管理评阅标准与评阅 Dify 的非敏感运行参数。API Key 与 Base URL 仍应优先通过环境变量配置。"
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
            {updateMutation.isSuccess ? <p className="text-emerald-600">评分标准已保存。</p> : null}
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
            <p>Workflow ID：{config?.workflow_id_configured ? "已配置" : "未配置"}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>编辑评分标准</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={submitRubric}>
            <Textarea value={draft} onChange={(event) => setDraft(event.target.value)} className="min-h-[260px]" />
            {updateMutation.isError ? <ErrorState message={(updateMutation.error as Error).message} /> : null}
            <Button type="submit" disabled={!draft.trim() || updateMutation.isPending}>
              {updateMutation.isPending ? "保存中..." : "保存评分标准"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>评阅 Dify 运行参数</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={submitConfig}>
            <div className="grid gap-4 md:grid-cols-2">
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
                  value={configForm.text_input_variable}
                  onChange={(event) => setConfigForm((current) => ({ ...current, text_input_variable: event.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">文件变量名</label>
                <Input
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
