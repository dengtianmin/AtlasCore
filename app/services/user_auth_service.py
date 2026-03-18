from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt_handler import create_access_token
from app.auth.password import hash_password, verify_password
from app.auth.rbac import ROLE_USER
from app.repositories.user_repo import UserRepository
from app.schemas.user import CurrentUserResponse, UserLoginRequest, UserRegisterRequest, UserTokenResponse


class UserAuthService:
    def __init__(self) -> None:
        self.user_repo = UserRepository()

    def register(self, db: Session, *, payload: UserRegisterRequest) -> CurrentUserResponse:
        existing = self.user_repo.get_by_student_id(db, payload.student_id)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student ID already registered")

        user = self.user_repo.create(
            db,
            student_id=payload.student_id,
            name=payload.name,
            password_hash=hash_password(payload.password),
            is_active=True,
        )
        db.commit()
        return self._to_current_user(user)

    def login(self, db: Session, *, payload: UserLoginRequest) -> UserTokenResponse:
        user = self.user_repo.get_by_student_id(db, payload.student_id)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

        self.user_repo.update_last_login(db, user=user, logged_in_at=datetime.now(UTC))
        db.commit()

        token, expires_in = create_access_token(
            subject=str(user.id),
            username=user.student_id,
            roles=[ROLE_USER],
            role=ROLE_USER,
            scope=ROLE_USER,
            token_type="user_access",
            student_id=user.student_id,
            name=user.name,
        )
        return UserTokenResponse(access_token=token, expires_in=expires_in)

    def get_current_user_payload(self, principal) -> CurrentUserResponse:
        return CurrentUserResponse(
            user_id=principal.user_id,
            student_id=principal.student_id or "",
            name=principal.name or "",
            roles=principal.roles,
        )

    def _to_current_user(self, user) -> CurrentUserResponse:
        return CurrentUserResponse(
            user_id=str(user.id),
            student_id=user.student_id,
            name=user.name,
            roles=[ROLE_USER],
        )
