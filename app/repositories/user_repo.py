from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def get_by_id(self, db: Session, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return db.execute(stmt).scalar_one_or_none()

    def get_by_student_id(self, db: Session, student_id: str) -> User | None:
        stmt = select(User).where(User.student_id == student_id)
        return db.execute(stmt).scalar_one_or_none()

    def create(
        self,
        db: Session,
        *,
        student_id: str,
        name: str,
        password_hash: str,
        is_active: bool = True,
    ) -> User:
        user = User(
            student_id=student_id,
            name=name,
            password_hash=password_hash,
            is_active=is_active,
        )
        db.add(user)
        db.flush()
        db.refresh(user)
        return user

    def update_last_login(self, db: Session, *, user: User, logged_in_at: datetime) -> User:
        user.last_login_at = logged_in_at
        db.add(user)
        db.flush()
        db.refresh(user)
        return user
