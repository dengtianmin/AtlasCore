from pydantic import BaseModel


class Principal(BaseModel):
    user_id: str
    username: str
    roles: list[str]
