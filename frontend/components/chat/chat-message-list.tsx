import { EmptyState } from "@/components/common/empty-state";

import { ChatMessageCard } from "./chat-message-card";

export type ChatTimelineMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt?: string;
};

export function ChatMessageList({ items }: { items: ChatTimelineMessage[] }) {
  if (!items.length) {
    return <EmptyState title="还没有提问记录" description="从一个研究问题开始，系统会在这里展示问答过程与返回结果。" />;
  }

  return (
    <div className="space-y-4">
      {items.map((item) => (
        <ChatMessageCard key={item.id} role={item.role} content={item.content} meta={item.createdAt} />
      ))}
    </div>
  );
}
