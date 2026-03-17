import { requestJson } from "@/lib/api/client";
import type { ReviewEvaluationResponse, ReviewRubric } from "@/types/api";

export function evaluateReview(answerText: string) {
  return requestJson<ReviewEvaluationResponse>("/review/evaluate", {
    method: "POST",
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
