from pydantic import BaseModel


class Principal(BaseModel):
    user_id: str
    username: str = ""
    student_id: str | None = None
    name: str | None = None
    roles: list[str]
    role: str = ""
    scope: str = ""
    token_type: str = ""
