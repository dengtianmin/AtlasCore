from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.admin_account import AdminAccount


class AdminAccountRepository:
    def get_by_id(self, db: Session, admin_id: UUID) -> AdminAccount | None:
        stmt = select(AdminAccount).where(AdminAccount.id == admin_id)
        return db.execute(stmt).scalar_one_or_none()

    def get_by_username(self, db: Session, username: str) -> AdminAccount | None:
        stmt = select(AdminAccount).where(AdminAccount.username == username)
        return db.execute(stmt).scalar_one_or_none()

    def create(self, db: Session, *, username: str, password_hash: str, is_active: bool = True) -> AdminAccount:
        admin = AdminAccount(username=username, password_hash=password_hash, is_active=is_active)
        db.add(admin)
        db.flush()
        db.refresh(admin)
        return admin
