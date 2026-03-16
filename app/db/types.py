from uuid import UUID

from sqlalchemy import String
from sqlalchemy.types import TypeDecorator


class GUID(TypeDecorator[str]):
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value: UUID | str | None, dialect) -> str | None:
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(UUID(str(value)))

    def process_result_value(self, value: str | None, dialect) -> UUID | None:
        if value is None:
            return None
        return UUID(str(value))
