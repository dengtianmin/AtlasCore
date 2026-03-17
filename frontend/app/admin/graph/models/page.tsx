"use client";

import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getModelSetting, updateModelSetting } from "@/lib/api/graph-extraction";
import { formatDateTime } from "@/lib/utils";

export default function AdminGraphModelsPage() {
  const queryClient = useQueryClient();
  const modelQuery = useQuery({ queryKey: ["graph-model-setting"], queryFn: getModelSetting });
  const [form, setForm] = useState({
    provider: "",
    model_name: "",
    api_base_url: "",
    api_key: "",
    enabled: true
  });
  const updateMutation = useMutation({
    mutationFn: updateModelSetting,
    onSuccess: async () => {
      setForm((current) => ({ ...current, api_key: "" }));
      await queryClient.invalidateQueries({ queryKey: ["graph-model-setting"] });
    }
  });

  useEffect(() => {
    if (modelQuery.data) {
      setForm({
        provider: modelQuery.data.provider,
        model_name: modelQuery.data.model_name,
        api_base_url: modelQuery.data.api_base_url ?? "",
        api_key: "",
        enabled: modelQuery.data.enabled
      });
    }
  }, [modelQuery.data]);

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    updateMutation.mutate(form);
  };

  if (modelQuery.isLoading) {
    return <LoadingState label="正在加载模型配置..." />;
  }
  if (modelQuery.isError) {
    return <ErrorState message={(modelQuery.error as Error).message} />;
  }

  const model = modelQuery.data ?? {
    provider: "",
    model_name: "",
    api_base_url: null,
    enabled: false,
    is_active: false,
    updated_at: null,
    updated_by: null,
    has_api_key: false
  };

  return (
    <div className="space-y-6">
      <PageHeader title="图谱提取模型" description="维护当前全局生效的提取模型配置。API Key 仅支持更新，不回显完整值。" />

      <Card>
        <CardHeader>
          <CardTitle>当前状态</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>已配置 API Key：{model.has_api_key ? "是" : "否"}</p>
          <p>最近更新时间：{formatDateTime(model.updated_at)}</p>
          <p>最近更新人：{model.updated_by ?? "未记录"}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>编辑模型配置</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={submit}>
            <Input placeholder="provider" value={form.provider} onChange={(event) => setForm((current) => ({ ...current, provider: event.target.value }))} />
            <Input placeholder="model_name" value={form.model_name} onChange={(event) => setForm((current) => ({ ...current, model_name: event.target.value }))} />
            <Input placeholder="api_base_url" value={form.api_base_url} onChange={(event) => setForm((current) => ({ ...current, api_base_url: event.target.value }))} />
            <Input type="password" placeholder={model.has_api_key ? "输入新 API Key 以覆盖" : "输入 API Key"} value={form.api_key} onChange={(event) => setForm((current) => ({ ...current, api_key: event.target.value }))} />
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={form.enabled} onChange={(event) => setForm((current) => ({ ...current, enabled: event.target.checked }))} />
              启用当前模型
            </label>
            <Button>{updateMutation.isPending ? "保存中..." : "保存模型配置"}</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
