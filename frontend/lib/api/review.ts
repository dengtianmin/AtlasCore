import { requestJson } from "@/lib/api/client";
import type {
  ReviewDifyConfigSummary,
  ReviewDifyConfigUpdateRequest,
  ReviewEvaluationResponse,
  ReviewLogListResponse,
  ReviewLogRecord,
  ReviewRubric
} from "@/types/api";

export function evaluateReview(answerText: string) {
  return requestJson<ReviewEvaluationResponse>("/review/evaluate", {
    method: "POST",
    auth: "user",
    body: { answer_text: answerText }
  });
}

export function getReviewRubric() {
  return requestJson<ReviewRubric>("/api/admin/review/rubric");
}

export function updateReviewRubric(rubricText: string) {
  return requestJson<ReviewRubric>("/api/admin/review/rubric", {
    method: "PUT",
    body: { rubric_text: rubricText }
  });
}

export function getReviewDifyConfig() {
  return requestJson<ReviewDifyConfigSummary>("/api/admin/review/config");
}

export function updateReviewDifyConfig(payload: ReviewDifyConfigUpdateRequest) {
  return requestJson<ReviewDifyConfigSummary>("/api/admin/review/config", {
    method: "PUT",
    body: payload
  });
}

export function listReviewLogs() {
  return requestJson<ReviewLogListResponse>("/api/admin/review/logs");
}

export function getReviewLog(recordId: string) {
  return requestJson<ReviewLogRecord>(`/api/admin/review/logs/${recordId}`);
}
