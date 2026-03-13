from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole


class UserRepository:
    def get_by_email(self, db: Session, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, db: Session, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return db.execute(stmt).scalar_one_or_none()

    def create(self, db: Session, *, email: str, password_hash: str) -> User:
        user = User(email=email, password_hash=password_hash, is_active=True)
        db.add(user)
        db.flush()
        return user

    def list_role_names(self, db: Session, user_id: UUID) -> list[str]:
        stmt = (
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        return list(db.execute(stmt).scalars().all())

    def assign_role(self, db: Session, *, user_id: UUID, role_id: UUID) -> None:
        db.add(UserRole(user_id=user_id, role_id=role_id))
