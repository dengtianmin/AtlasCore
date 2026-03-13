from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.jwt_handler import create_access_token
from app.auth.password import hash_password, verify_password
from app.auth.principal import Principal
from app.auth.rbac import ROLE_USER
from app.repositories.role_repo import RoleRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import TokenResponse


class AuthService:
    def __init__(self) -> None:
        self.user_repo = UserRepository()
        self.role_repo = RoleRepository()

    def register(self, db: Session, *, email: str, password: str) -> TokenResponse:
        if self.user_repo.get_by_email(db, email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

        roles = self.role_repo.ensure_default_roles(db)

        user = self.user_repo.create(db, email=email, password_hash=hash_password(password))
        self.user_repo.assign_role(db, user_id=user.id, role_id=roles[ROLE_USER].id)

        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User creation failed") from exc

        role_names = self.user_repo.list_role_names(db, user.id)
        token, expires_in = create_access_token(subject=str(user.id), email=user.email, roles=role_names)
        return TokenResponse(access_token=token, expires_in=expires_in)

    def login(self, db: Session, *, email: str, password: str) -> TokenResponse:
        user = self.user_repo.get_by_email(db, email)
        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

        roles = self.user_repo.list_role_names(db, user.id)
        token, expires_in = create_access_token(subject=str(user.id), email=user.email, roles=roles)
        return TokenResponse(access_token=token, expires_in=expires_in)

    def get_current_user_payload(self, principal: Principal) -> dict:
        return {
            "user_id": principal.user_id,
            "email": principal.email,
            "roles": principal.roles,
        }
