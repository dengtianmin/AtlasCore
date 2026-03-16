import { requestJson } from "@/lib/api/client";
import type { ChatResponse, FeedbackResponse } from "@/types/api";

export function sendChatMessage(payload: { question: string; session_id?: string | null }) {
  return requestJson<ChatResponse>("/chat/messages", {
    method: "POST",
    body: payload,
    token: ""
  });
}

export function submitChatFeedback(
  messageId: string,
  payload: { rating?: number | null; liked?: boolean | null; comment?: string | null; source?: string }
) {
  return requestJson<FeedbackResponse>(`/chat/messages/${messageId}/feedback`, {
    method: "POST",
    body: payload,
    token: ""
  });
}
