from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt_handler import create_access_token
from app.auth.password import hash_password, verify_password
from app.auth.principal import Principal
from app.auth.rbac import ROLE_ADMIN
from app.repositories.admin_account_repo import AdminAccountRepository
from app.schemas.auth import TokenResponse


class AuthService:
    def __init__(self) -> None:
        self.admin_repo = AdminAccountRepository()

    def login(self, db: Session, *, username: str, password: str) -> TokenResponse:
        admin = self.admin_repo.get_by_username(db, username)
        if admin is None or not verify_password(password, admin.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not admin.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin is inactive")

        token, expires_in = create_access_token(
            subject=str(admin.id),
            username=admin.username,
            roles=[ROLE_ADMIN],
            role=ROLE_ADMIN,
            scope=ROLE_ADMIN,
            token_type="admin_access",
        )
        return TokenResponse(access_token=token, expires_in=expires_in)

    def ensure_admin_account(
        self,
        db: Session,
        *,
        username: str,
        password: str,
    ) -> None:
        if self.admin_repo.get_by_username(db, username) is not None:
            return
        self.admin_repo.create(db, username=username, password_hash=hash_password(password), is_active=True)
        db.commit()

    def get_current_user_payload(self, principal: Principal) -> dict:
        return {
            "admin_id": principal.user_id,
            "username": principal.username,
            "roles": principal.roles,
        }
