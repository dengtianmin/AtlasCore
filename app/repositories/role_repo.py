from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.rbac import ROLE_ADMIN, ROLE_USER
from app.models.role import Role


class RoleRepository:
    def get_by_name(self, db: Session, name: str) -> Role | None:
        stmt = select(Role).where(Role.name == name)
        return db.execute(stmt).scalar_one_or_none()

    def create(self, db: Session, *, name: str, description: str | None = None) -> Role:
        role = Role(name=name, description=description)
        db.add(role)
        db.flush()
        return role

    def ensure_default_roles(self, db: Session) -> dict[str, Role]:
        roles: dict[str, Role] = {}
        for name, desc in [
            (ROLE_USER, "Standard user role"),
            (ROLE_ADMIN, "Administrator role"),
        ]:
            role = self.get_by_name(db, name)
            if role is None:
                role = self.create(db, name=name, description=desc)
            roles[name] = role
        return roles
