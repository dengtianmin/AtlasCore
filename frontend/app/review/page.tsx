"use client";

import { FormEvent, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { ErrorState } from "@/components/common/error-state";
import { PageHeader } from "@/components/common/page-header";
import { PublicHeader } from "@/components/common/public-header";
import { ReviewMessageList, type ReviewTimelineMessage } from "@/components/review/review-message-list";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { evaluateReview } from "@/lib/api/review";

export default function ReviewPage() {
  const [answerText, setAnswerText] = useState("");
  const [messages, setMessages] = useState<ReviewTimelineMessage[]>([]);

  const reviewMutation = useMutation({
    mutationFn: evaluateReview,
    onMutate: (content) => {
      const createdAt = new Date().toISOString();
      setMessages((current) => [
        ...current,
        {
          id: `user-${crypto.randomUUID()}`,
          role: "user",
          type: "text",
          content,
          createdAt,
        },
      ]);
      return { createdAt };
    },
    onSuccess: (payload, _content, context) => {
      setMessages((current) => [
        ...current,
        {
          id: payload.review_log_id || `assistant-${crypto.randomUUID()}`,
          role: "assistant",
          type: "review_result",
          createdAt: payload.created_at || context?.createdAt || new Date().toISOString(),
          data: payload,
        },
      ]);
      setAnswerText("");
    },
  });

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!answerText.trim() || reviewMutation.isPending) {
      return;
    }
    await reviewMutation.mutateAsync(answerText.trim());
  };

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#f7f8fa_0%,#eef2f6_100%)]" style={{ fontFamily: "PingFang SC, Microsoft YaHei, Noto Sans SC, sans-serif" }}>
      <PublicHeader />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <PageHeader
          title="评阅"
          description="评阅页保持聊天式体验：你的方案先进入消息流，AtlasCore 再返回一条结构化评阅消息。"
        />

        <div className="mt-6 grid gap-6 xl:grid-cols-[1fr_320px]">
          <Card className="border-slate-200 bg-white/70 backdrop-blur">
            <CardHeader>
              <CardTitle>评阅对话</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {reviewMutation.isError ? <ErrorState message={(reviewMutation.error as Error).message} /> : null}
              <ReviewMessageList items={messages} />
            </CardContent>
          </Card>

          <div className="space-y-6">
            <Card className="border-slate-200 bg-white/80">
              <CardHeader>
                <CardTitle>提交方案</CardTitle>
              </CardHeader>
              <CardContent>
                <form className="space-y-4" onSubmit={submit}>
                  <Textarea
                    value={answerText}
                    onChange={(event) => setAnswerText(event.target.value)}
                    placeholder="输入需要评阅的方案、说明或答题内容。"
                    className="min-h-[240px]"
                  />
                  <p className="text-sm leading-6 text-slate-500">
                    系统将通过 AtlasCore 调用独立评阅 Dify，并在消息流中返回单条结构化评阅结果。
                  </p>
                  <Button className="w-full" type="submit" disabled={!answerText.trim() || reviewMutation.isPending}>
                    {reviewMutation.isPending ? "评阅中..." : "开始评阅"}
                  </Button>
                </form>
              </CardContent>
            </Card>

            <Card className="border-slate-200 bg-white/80">
              <CardHeader>
                <CardTitle>展示规则</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm leading-6 text-slate-600">
                <p>评分、总体结论、审核详情、关键问题和扣分依据都集中在同一条 AI 消息内展示。</p>
                <p>当结构化数据缺失时，页面会自动降级显示总结或原始文本，不会白屏。</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
