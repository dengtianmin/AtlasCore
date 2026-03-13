from pydantic import BaseModel


class DifyDocumentIndexRequest(BaseModel):
    document_id: str
    title: str
    source_uri: str | None = None


class DifyJobResponse(BaseModel):
    job_id: str
    status: str
    message: str
