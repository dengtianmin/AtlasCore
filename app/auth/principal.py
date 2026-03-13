from pydantic import BaseModel


class Principal(BaseModel):
    user_id: str
    email: str
    roles: list[str]
