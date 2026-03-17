from enum import StrEnum


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    REGISTERED = "registered"
    PENDING_EXTRACTION = "pending_extraction"
    EXTRACTING = "extracting"
    EXTRACTION_FAILED = "extraction_failed"
    EXTRACTED_NOT_APPLIED = "extracted_not_applied"
    APPLIED_TO_GRAPH = "applied_to_graph"
    REMOVED_FROM_CURRENT_GRAPH = "removed_from_current_graph"
    SUPERSEDED = "superseded"
    SYNCING = "syncing"
    SYNCED = "synced"
    INDEXED = "indexed"
    GRAPH_PENDING = "graph_pending"
    GRAPH_SYNCED = "graph_synced"
    FAILED = "failed"
