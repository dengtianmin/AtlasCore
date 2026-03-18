from pydantic import BaseModel, Field

STUDENT_ID_PATTERN = r"^\d{10}$"
CHINESE_NAME_PATTERN = r"^[\u4e00-\u9fff]+$"


class UserRegisterRequest(BaseModel):
    student_id: str = Field(pattern=STUDENT_ID_PATTERN)
    name: str = Field(pattern=CHINESE_NAME_PATTERN)
    password: str = Field(min_length=8, max_length=128)


class UserLoginRequest(BaseModel):
    student_id: str = Field(pattern=STUDENT_ID_PATTERN)
    password: str = Field(min_length=1, max_length=128)


class UserTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class CurrentUserResponse(BaseModel):
    user_id: str
    student_id: str
    name: str
    roles: list[str]
