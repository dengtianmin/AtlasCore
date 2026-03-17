"use client";

import { FormEvent, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { ErrorState } from "@/components/common/error-state";
import { PageHeader } from "@/components/common/page-header";
import { PublicHeader } from "@/components/common/public-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { evaluateReview } from "@/lib/api/review";

export default function ReviewPage() {
  const [answerText, setAnswerText] = useState("");
  const reviewMutation = useMutation({
    mutationFn: evaluateReview
  });

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!answerText.trim() || reviewMutation.isPending) {
      return;
    }
    await reviewMutation.mutateAsync(answerText.trim());
  };

  return (
    <div>
      <PublicHeader />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <PageHeader title="评阅" description="输入你的答案，系统将基于当前生效的评分标准返回分数与评语。" />
        <div className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <Card>
            <CardHeader>
              <CardTitle>答案输入</CardTitle>
            </CardHeader>
            <CardContent>
              <form className="space-y-4" onSubmit={submit}>
                <Textarea
                  value={answerText}
                  onChange={(event) => setAnswerText(event.target.value)}
                  placeholder="请输入需要评阅的答案内容"
                  className="min-h-[320px]"
                />
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm text-muted-foreground">分数范围固定为 0-100，评语将围绕管理员配置的评分标准生成。</p>
                  <Button type="submit" disabled={!answerText.trim() || reviewMutation.isPending}>
                    {reviewMutation.isPending ? "评阅中..." : "开始评阅"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>评阅结果</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {reviewMutation.isError ? <ErrorState message={(reviewMutation.error as Error).message} /> : null}
              {reviewMutation.data ? (
                <div className="space-y-4">
                  <div className="rounded-lg border bg-panel p-4">
                    <p className="text-sm text-muted-foreground">分数</p>
                    <p className="mt-2 text-3xl font-semibold">{reviewMutation.data.score}</p>
                  </div>
                  <div className="rounded-lg border bg-panel p-4">
                    <p className="text-sm text-muted-foreground">打分理由</p>
                    <p className="mt-2 whitespace-pre-wrap text-sm leading-6">{reviewMutation.data.reason}</p>
                  </div>
                </div>
              ) : (
                <div className="rounded-lg border border-dashed bg-panel/60 p-6 text-sm text-muted-foreground">
                  提交答案后，这里会显示结构化的评阅结果。
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
