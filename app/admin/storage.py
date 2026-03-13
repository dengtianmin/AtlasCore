from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings


class DocumentStorage:
    """Local placeholder storage for V1.

    Future versions can replace this with Azure Blob Storage implementation
    behind the same interface.
    """

    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.DOCUMENT_LOCAL_STORAGE_DIR)

    def save(self, upload: UploadFile) -> tuple[str, int]:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        safe_name = upload.filename or f"unnamed-{uuid4().hex}.bin"
        object_name = f"{uuid4().hex}-{safe_name}"
        full_path = self.base_dir / object_name

        data = upload.file.read()
        full_path.write_bytes(data)

        return str(full_path), len(data)
