"use client";

import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { PageHeader } from "@/components/common/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { listDifyDebugLogs, runDifyDebug } from "@/lib/api/system";
import type { DifyDebugRequest } from "@/types/api";

function renderJson(value: unknown) {
  return JSON.stringify(value ?? {}, null, 2);
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleString("zh-CN");
}

export default function AdminDifyDebugPage() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<DifyDebugRequest>({
    base_url: "",
    api_key: "",
    timeout_seconds: 15,
    workflow_id: "",
    response_mode: "blocking",
    text_input_variable: "",
    file_input_variable: "",
    enable_trace: true,
    user_prefix: "debug",
    sample_text: ""
  });

  const logsQuery = useQuery({
    queryKey: ["admin-dify-debug-logs"],
    queryFn: () => listDifyDebugLogs(20)
  });

  const debugMutation = useMutation({
    mutationFn: runDifyDebug,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-dify-debug-logs"] });
    }
  });

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    debugMutation.mutate({
      ...form,
      workflow_id: form.workflow_id?.trim() || null,
      text_input_variable: form.text_input_variable?.trim() || null,
      file_input_variable: form.file_input_variable?.trim() || null,
      sample_text: form.sample_text?.trim() || null
    });
  };

  const result = debugMutation.data;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dify 调试"
        description="管理员可在这里临时提交 Dify Base URL 与 API Key，执行参数校验、应用信息探测与 Workflow 冒烟测试。每次调试都会写入后端 JSONL 日志，便于后续定位问题。"
        actions={
          <Button variant="secondary" onClick={() => logsQuery.refetch()} disabled={logsQuery.isFetching}>
            {logsQuery.isFetching ? "刷新中..." : "刷新日志"}
          </Button>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <Card>
          <CardHeader>
            <div>
              <CardTitle>连接参数</CardTitle>
              <p className="mt-1 text-sm text-muted-foreground">必填项只有 `base_url` 与 `api_key`。若你想直接联调 workflow，建议再补 `workflow_id`、文本变量名和一段测试输入。</p>
            </div>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={submit}>
              <div className="space-y-2">
                <label className="text-sm font-medium">Base URL</label>
                <Input
                  placeholder="https://api.dify.ai"
                  value={form.base_url}
                  onChange={(event) => setForm((current) => ({ ...current, base_url: event.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">API Key</label>
                <Input
                  type="password"
                  placeholder="app-..."
                  value={form.api_key}
                  onChange={(event) => setForm((current) => ({ ...current, api_key: event.target.value }))}
                />
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Workflow ID</label>
                  <Input
                    placeholder="可选"
                    value={form.workflow_id ?? ""}
                    onChange={(event) => setForm((current) => ({ ...current, workflow_id: event.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Timeout</label>
                  <Input
                    type="number"
                    min={1}
                    max={120}
                    value={form.timeout_seconds ?? 15}
                    onChange={(event) =>
                      setForm((current) => ({ ...current, timeout_seconds: Number(event.target.value || 15) }))
                    }
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">文本变量名</label>
                  <Input
                    placeholder="例如 query / question"
                    value={form.text_input_variable ?? ""}
                    onChange={(event) => setForm((current) => ({ ...current, text_input_variable: event.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">文件变量名</label>
                  <Input
                    placeholder="可选"
                    value={form.file_input_variable ?? ""}
                    onChange={(event) => setForm((current) => ({ ...current, file_input_variable: event.target.value }))}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">测试文本</label>
                <Textarea
                  placeholder="如果你填了文本变量名，这里可以直接跑一次 blocking workflow。"
                  value={form.sample_text ?? ""}
                  onChange={(event) => setForm((current) => ({ ...current, sample_text: event.target.value }))}
                />
              </div>
              <div className="flex items-center justify-between rounded-lg border bg-muted/30 px-4 py-3 text-sm">
                <div>
                  <p className="font-medium">建议补充的内容</p>
                  <p className="mt-1 text-muted-foreground">最小调试只要 `base_url` + `api_key`。若要真正判断 workflow 输入是否匹配，最好再补 `text_input_variable`，必要时补 `workflow_id`。</p>
                </div>
              </div>
              <Button className="w-full" disabled={debugMutation.isPending || !form.base_url || !form.api_key}>
                {debugMutation.isPending ? "正在调试..." : "开始调试"}
              </Button>
              {debugMutation.isError ? <p className="text-sm text-destructive">{(debugMutation.error as Error).message}</p> : null}
            </form>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>联调结果</CardTitle>
                <p className="mt-1 text-sm text-muted-foreground">先看 reachability 和 validation，再判断是否需要补 workflow 变量或 sample text。</p>
              </div>
              {result ? (
                <Badge variant={result.validation_ok ? "success" : result.reachable ? "warning" : "destructive"}>
                  {result.validation_ok ? "Validation OK" : result.reachable ? "Reachable" : "Failed"}
                </Badge>
              ) : null}
            </CardHeader>
            <CardContent className="space-y-4">
              {!result && !debugMutation.isPending ? <ErrorState message="还没有执行 Dify 调试。提交一次参数后，这里会展示校验结果和 Workflow 回包摘要。" /> : null}
              {debugMutation.isPending ? <LoadingState label="正在请求 Dify..." /> : null}
              {result ? (
                <>
                  <div className="grid gap-3 md:grid-cols-2">
                    <div className="rounded-lg border bg-muted/40 p-4">
                      <p className="text-xs uppercase tracking-wide text-muted-foreground">Reachable</p>
                      <p className="mt-2 text-lg font-semibold">{result.reachable ? "Yes" : "No"}</p>
                    </div>
                    <div className="rounded-lg border bg-muted/40 p-4">
                      <p className="text-xs uppercase tracking-wide text-muted-foreground">Validation</p>
                      <p className="mt-2 text-lg font-semibold">{result.validation_ok ? "Passed" : "Needs Attention"}</p>
                    </div>
                  </div>
                  <div className="rounded-lg border bg-muted/40 p-4 text-sm">
                    <p className="font-medium">日志文件</p>
                    <p className="mt-1 break-all text-muted-foreground">{result.logs_saved_to}</p>
                  </div>
                  {result.warnings.length ? (
                    <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                      <p className="font-medium">警告</p>
                      <ul className="mt-2 space-y-1">
                        {result.warnings.map((warning) => (
                          <li key={warning}>- {warning}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  <div className="grid gap-4">
                    <div>
                      <p className="mb-2 text-sm font-medium">应用信息</p>
                      <pre className="overflow-x-auto rounded-lg border bg-slate-950 p-4 text-xs text-slate-100">{renderJson(result.info)}</pre>
                    </div>
                    <div>
                      <p className="mb-2 text-sm font-medium">Parameters</p>
                      <pre className="overflow-x-auto rounded-lg border bg-slate-950 p-4 text-xs text-slate-100">{renderJson(result.parameters)}</pre>
                    </div>
                    {result.workflow_result ? (
                      <div>
                        <p className="mb-2 text-sm font-medium">Workflow 结果</p>
                        <pre className="overflow-x-auto rounded-lg border bg-slate-950 p-4 text-xs text-slate-100">{renderJson(result.workflow_result)}</pre>
                      </div>
                    ) : null}
                  </div>
                </>
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div>
                <CardTitle>最近调试日志</CardTitle>
                <p className="mt-1 text-sm text-muted-foreground">每次调试都会保存安全摘要，不含 API Key。这里展示最近 20 条，方便回看联调过程。</p>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {logsQuery.isLoading ? <LoadingState label="正在加载调试日志..." /> : null}
              {logsQuery.isError ? <ErrorState message={(logsQuery.error as Error).message} /> : null}
              {!logsQuery.isLoading && !logsQuery.isError && logsQuery.data?.items.length === 0 ? (
                <ErrorState message="当前还没有 Dify 调试日志。" />
              ) : null}
              {logsQuery.data?.items.map((item) => (
                <div key={`${item.recorded_at}-${item.status}`} className="rounded-lg border bg-panel p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-medium">{item.event}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{formatDateTime(item.recorded_at)}</p>
                    </div>
                    <Badge variant={item.status === "success" ? "success" : item.status === "partial_failure" ? "warning" : "destructive"}>
                      {item.status}
                    </Badge>
                  </div>
                  <pre className="mt-3 overflow-x-auto rounded-lg bg-slate-950 p-4 text-xs text-slate-100">{renderJson(item.payload)}</pre>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
