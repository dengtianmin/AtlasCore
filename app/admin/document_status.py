from enum import StrEnum


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    INDEXED = "indexed"
    GRAPH_PENDING = "graph_pending"
    GRAPH_SYNCED = "graph_synced"
    FAILED = "failed"
