"use client";

import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ErrorState } from "@/components/common/error-state";
import { LoadingState } from "@/components/common/loading-state";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { getReviewRubric, updateReviewRubric } from "@/lib/api/review";
import { formatDateTime } from "@/lib/utils";

export default function AdminReviewRubricPage() {
  const queryClient = useQueryClient();
  const rubricQuery = useQuery({
    queryKey: ["review-rubric"],
    queryFn: getReviewRubric
  });
  const [draft, setDraft] = useState("");

  const updateMutation = useMutation({
    mutationFn: updateReviewRubric,
    onSuccess: async (payload) => {
      setDraft(payload.rubric_text);
      await queryClient.invalidateQueries({ queryKey: ["review-rubric"] });
    }
  });

  useEffect(() => {
    if (rubricQuery.data) {
      setDraft(rubricQuery.data.rubric_text);
    }
  }, [rubricQuery.data]);

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    updateMutation.mutate(draft.trim());
  };

  if (rubricQuery.isLoading) {
    return <LoadingState label="正在加载评分标准..." />;
  }
  if (rubricQuery.isError) {
    return <ErrorState message={(rubricQuery.error as Error).message} />;
  }

  const rubric = rubricQuery.data ?? {
    rubric_text: "",
    updated_at: null,
    updated_by: null,
    is_active: false
  };

  return (
    <div className="space-y-6">
      <PageHeader title="评分标准" description="维护当前生效的评阅评分标准。第一版只保留一条当前内容，不做多版本切换。" />

      <Card>
        <CardHeader>
          <CardTitle>当前状态</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>当前状态：{rubric.is_active ? "已生效" : "未配置"}</p>
          <p>最近更新时间：{formatDateTime(rubric.updated_at)}</p>
          <p>最近更新人：{rubric.updated_by ?? "未记录"}</p>
          {updateMutation.isSuccess ? <p className="text-emerald-600">保存成功，后续评阅请求将按新标准执行。</p> : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>编辑评分标准</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={submit}>
            <Textarea value={draft} onChange={(event) => setDraft(event.target.value)} className="min-h-[300px]" />
            {updateMutation.isError ? <ErrorState message={(updateMutation.error as Error).message} /> : null}
            <Button type="submit" disabled={!draft.trim() || updateMutation.isPending}>
              {updateMutation.isPending ? "保存中..." : "保存评分标准"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
