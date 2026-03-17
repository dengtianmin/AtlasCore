"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { PageHeader } from "@/components/common/page-header";
import { PublicHeader } from "@/components/common/public-header";
import { FeedbackActions } from "@/components/chat/feedback-actions";
import { ChatInput } from "@/components/chat/chat-input";
import { ChatMessageList, type ChatTimelineMessage } from "@/components/chat/chat-message-list";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { sendChatMessage, submitChatFeedback } from "@/lib/api/chat";

export default function ChatPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatTimelineMessage[]>([]);
  const [lastAssistantMessageId, setLastAssistantMessageId] = useState<string | null>(null);

  const chatMutation = useMutation({
    mutationFn: (question: string) => sendChatMessage({ question, session_id: sessionId }),
    onMutate: (question) => {
      const createdAt = new Date().toISOString();
      const userMessageId = `user-${crypto.randomUUID()}`;
      const assistantMessageId = `pending-${crypto.randomUUID()}`;

      setMessages((current) => [
        ...current,
        { id: userMessageId, role: "user", content: question, createdAt },
        {
          id: assistantMessageId,
          role: "assistant",
          content: "AtlasCore 正在通过后端调用 Dify，请稍候...",
          createdAt,
          source: "atlascore",
          status: "processing"
        }
      ]);

      return { assistantMessageId };
    },
    onSuccess: (response, _question, context) => {
      setSessionId(response.session_id);
      setLastAssistantMessageId(response.message_id);
      setMessages((current) => [
        ...current.filter((message) => message.id !== context?.assistantMessageId),
        {
          id: response.message_id,
          role: "assistant",
          content: response.answer,
          createdAt: response.created_at,
          source: response.source,
          status: response.status,
          providerMessageId: response.provider_message_id,
          workflowRunId: response.workflow_run_id
        }
      ]);
    },
    onError: (error, _question, context) => {
      setLastAssistantMessageId(null);
      setMessages((current) =>
        current.map((message) =>
          message.id === context?.assistantMessageId
            ? {
                ...message,
                content: `请求失败：${(error as Error).message}`,
                status: "failed",
                source: "atlascore"
              }
            : message
        )
      );
    }
  });

  const feedbackMutation = useMutation({
    mutationFn: ({ liked }: { liked: boolean }) =>
      lastAssistantMessageId ? submitChatFeedback(lastAssistantMessageId, { liked, source: "frontend" }) : Promise.resolve(null)
  });

  return (
    <div>
      <PublicHeader />
      <main className="mx-auto max-w-7xl px-6 py-10">
        <PageHeader title="聊天问答" description="普通用户通过 AtlasCore 统一聊天接口提问。第一版提供单会话体验，并为后续多会话扩展预留结构。" />
        <div className="mt-6 grid gap-6 xl:grid-cols-[260px_1fr]">
          <Card className="h-fit">
            <CardHeader>
              <CardTitle>会话列表</CardTitle>
            </CardHeader>
            <CardContent>
              {sessionId ? (
                <div className="rounded-lg border bg-panel p-3 text-sm">
                  <p className="font-medium">当前会话</p>
                  <p className="mt-1 break-all text-xs text-muted-foreground">{sessionId}</p>
                </div>
              ) : (
                <EmptyState title="尚未开始" description="第一版采用轻量单会话模式。发送第一个问题后会创建会话。" />
              )}
            </CardContent>
          </Card>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>对话流</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {chatMutation.isError ? <ErrorState message={(chatMutation.error as Error).message} /> : null}
                <ChatMessageList items={messages} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>输入与反馈</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <ChatInput
                  isPending={chatMutation.isPending}
                  onSubmit={async (value) => {
                    try {
                      await chatMutation.mutateAsync(value);
                      return true;
                    } catch {
                      return false;
                    }
                  }}
                />
                <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-panel p-4">
                  <div>
                    <p className="text-sm font-medium">结果反馈</p>
                    <p className="text-xs leading-5 text-muted-foreground">支持点赞、点踩和后续评分扩展。当前反馈会写回 AtlasCore。</p>
                  </div>
                  <FeedbackActions
                    disabled={!lastAssistantMessageId || feedbackMutation.isPending}
                    onLike={() => feedbackMutation.mutate({ liked: true })}
                    onDislike={() => feedbackMutation.mutate({ liked: false })}
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
