"use client";

import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { getPromptSetting, updatePromptSetting } from "@/lib/api/graph-extraction";
import { formatDateTime } from "@/lib/utils";

export default function AdminGraphPromptPage() {
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState("");
  const promptQuery = useQuery({
    queryKey: ["graph-prompt-setting"],
    queryFn: getPromptSetting
  });
  const updateMutation = useMutation({
    mutationFn: updatePromptSetting,
    onSuccess: async (payload) => {
      setDraft(payload.prompt_text);
      await queryClient.invalidateQueries({ queryKey: ["graph-prompt-setting"] });
    }
  });

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    updateMutation.mutate(draft);
  };

  if (promptQuery.isLoading) {
    return <LoadingState label="正在加载 Prompt 配置..." />;
  }
  if (promptQuery.isError) {
    return <ErrorState message={(promptQuery.error as Error).message} />;
  }

  const prompt = promptQuery.data ?? {
    prompt_text: "",
    updated_at: null,
    updated_by: null,
    is_active: false
  };

  return (
    <div className="space-y-6">
      <PageHeader title="图谱提取 Prompt" description="维护当前全局生效的抽取 Prompt。第一版不做复杂版本管理，只保留当前内容。" />

      <Card>
        <CardHeader>
          <CardTitle>当前配置</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>最近更新时间：{formatDateTime(prompt.updated_at)}</p>
          <p>最近更新人：{prompt.updated_by ?? "system"}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>编辑 Prompt</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={submit}>
            <Textarea value={draft || prompt.prompt_text} onChange={(event) => setDraft(event.target.value)} className="min-h-[280px]" />
            <Button>{updateMutation.isPending ? "保存中..." : "保存 Prompt"}</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
