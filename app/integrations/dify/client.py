from typing import Protocol
from uuid import uuid4

from app.core.config import settings
from app.integrations.dify.schemas import DifyDocumentIndexRequest, DifyJobResponse


class DifyClientProtocol(Protocol):
    def is_enabled(self) -> bool:
        ...

    def enqueue_document_index(self, payload: DifyDocumentIndexRequest) -> DifyJobResponse:
        ...


class DifyClient:
    """Placeholder Dify client.

    V1 behavior:
    - No network call.
    - Works even without DIFY_BASE_URL / DIFY_API_KEY.
    - Returns predictable queued response for orchestration.

    Future behavior:
    - Replace enqueue_document_index internals with real HTTP call.
    """

    def is_enabled(self) -> bool:
        return bool(settings.DIFY_BASE_URL and settings.DIFY_API_KEY)

    def enqueue_document_index(self, payload: DifyDocumentIndexRequest) -> DifyJobResponse:
        if not self.is_enabled():
            return DifyJobResponse(
                job_id=f"placeholder-{payload.document_id}",
                status="queued",
                message="Dify integration is not configured; queued as placeholder only",
            )

        # Placeholder-only for this stage. Real HTTP call will be added later.
        return DifyJobResponse(
            job_id=f"dify-{uuid4().hex}",
            status="queued",
            message="Dify integration configured; real API call not implemented in this stage",
        )


def get_dify_client() -> DifyClientProtocol:
    return DifyClient()
