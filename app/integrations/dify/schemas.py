from pydantic import BaseModel, Field


class DifyDocumentIndexRequest(BaseModel):
    document_id: str
    title: str
    source_uri: str | None = None


class DifyJobResponse(BaseModel):
    job_id: str
    status: str
    message: str


class DifyChatRequest(BaseModel):
    query: str
    session_id: str
    user: str = "anonymous"


class DifyChatSource(BaseModel):
    title: str
    snippet: str | None = None
    source: str | None = None


class DifyChatResponse(BaseModel):
    answer: str
    source: str = "dify"
    sources: list[DifyChatSource] = Field(default_factory=list)
    retrieved_context: str | None = None
    session_id: str | None = None
    provider_message_id: str | None = None
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
