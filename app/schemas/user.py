from pydantic import BaseModel


class UserRead(BaseModel):
    id: str
    username: str
    is_active: bool
