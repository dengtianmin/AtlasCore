import { ApiError, requestEventStream, requestJson } from "@/lib/api/client";
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

type ChatStreamEvent =
  | { event: "start"; data: { session_id: string; provider_message_id?: string | null; workflow_run_id?: string | null } }
  | { event: "delta"; data: { text: string } }
  | {
      event: "end";
      data: {
        message_id: string;
        session_id: string;
        status: string;
        provider_message_id?: string | null;
        workflow_run_id?: string | null;
        created_at: string;
      };
    }
  | { event: "error"; data: { detail: string } };

export type ChatStreamEndPayload = Extract<ChatStreamEvent, { event: "end" }>["data"];

export async function streamChatMessage(
  payload: { question: string; session_id?: string | null },
  options: { onEvent: (event: ChatStreamEvent) => void }
) {
  let finalResponse: ChatStreamEndPayload | null = null;
  let streamError: string | null = null;

  await requestEventStream("/chat/messages/stream", {
    method: "POST",
    body: payload,
    token: "",
    onEvent: (event) => {
      const typedEvent = event as ChatStreamEvent;
      options.onEvent(typedEvent);
      if (typedEvent.event === "end") {
        finalResponse = typedEvent.data;
      }
      if (typedEvent.event === "error") {
        streamError = typedEvent.data.detail;
      }
    }
  });

  if (streamError) {
    throw new ApiError(502, streamError);
  }

  if (!finalResponse) {
    throw new ApiError(500, "流式响应未正常结束");
  }

  return finalResponse;
}
