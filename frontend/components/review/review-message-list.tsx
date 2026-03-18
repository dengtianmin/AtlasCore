import { EmptyState } from "@/components/common/empty-state";
import { ChatMessageCard } from "@/components/chat/chat-message-card";
import type { ReviewEvaluationResponse } from "@/types/api";

import { ReviewMessageCard } from "./review-message-card";

export type ReviewTimelineMessage =
  | {
      id: string;
      role: "user" | "assistant";
      type: "text";
      content: string;
      createdAt: string;
    }
  | {
      id: string;
      role: "assistant";
      type: "review_result";
      createdAt: string;
      data: ReviewEvaluationResponse;
    };

export function ReviewMessageList({ items }: { items: ReviewTimelineMessage[] }) {
  if (!items.length) {
    return <EmptyState title="还没有评阅记录" description="输入待评阅方案后，这里会以聊天消息流的方式展示你的输入和结构化评阅结果。" />;
  }

  return (
    <div className="space-y-4">
      {items.map((item) =>
        item.type === "text" ? (
          <ChatMessageCard key={item.id} role={item.role} content={item.content} meta={item.createdAt} />
        ) : (
          <ReviewMessageCard key={item.id} data={item.data} meta={item.createdAt} />
        )
      )}
    </div>
  );
}
