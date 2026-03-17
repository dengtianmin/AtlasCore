from enum import StrEnum


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    SYNCING = "syncing"
    SYNCED = "synced"
    INDEXED = "indexed"
    GRAPH_PENDING = "graph_pending"
    GRAPH_SYNCED = "graph_synced"
    FAILED = "failed"
