from pydantic import BaseModel


class UserRead(BaseModel):
    id: str
    email: str
    is_active: bool
