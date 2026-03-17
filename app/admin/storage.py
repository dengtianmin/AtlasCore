from dataclasses import dataclass
import mimetypes
from pathlib import Path
import re
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings


@dataclass(slots=True)
class StoredDocument:
    local_path: str
    file_size: int
    mime_type: str
    file_extension: str | None
    stored_filename: str


class DocumentStorage:
    """Local placeholder storage for V1.

    Future versions can replace this with Azure Blob Storage implementation
    behind the same interface.
    """

    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.DOCUMENT_LOCAL_STORAGE_DIR)

    @staticmethod
    def _sanitize_filename(filename: str | None) -> str:
        raw_name = (filename or "").strip()
        basename = Path(raw_name).name
        sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", basename).strip("._")
        return sanitized or f"unnamed-{uuid4().hex}.bin"

    def save(self, upload: UploadFile) -> StoredDocument:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        safe_name = self._sanitize_filename(upload.filename)
        object_name = f"{uuid4().hex}-{safe_name}"
        full_path = self.base_dir / object_name

        data = upload.file.read()
        full_path.write_bytes(data)

        suffix = Path(safe_name).suffix.lower()
        mime_type = upload.content_type or mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
        return StoredDocument(
            local_path=str(full_path),
            file_size=len(data),
            mime_type=mime_type,
            file_extension=suffix[1:] if suffix else None,
            stored_filename=object_name,
        )

    def delete(self, local_path: str | None) -> None:
        if not local_path:
            return
        path = Path(local_path).expanduser().resolve()
        base_dir = self.base_dir.expanduser().resolve()
        try:
            path.relative_to(base_dir)
        except ValueError as exc:
            raise ValueError("Refusing to delete file outside document storage directory") from exc
        if path.exists():
            path.unlink()
