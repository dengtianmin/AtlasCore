from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.review_dify_setting import ReviewDifySetting


class ReviewDifySettingRepository:
    def get_active(self, db: Session) -> ReviewDifySetting | None:
        stmt = select(ReviewDifySetting).where(ReviewDifySetting.is_active.is_(True)).order_by(ReviewDifySetting.updated_at.desc())
        return db.execute(stmt).scalar_one_or_none()

    def replace_active(self, db: Session, *, setting: ReviewDifySetting) -> ReviewDifySetting:
        db.execute(update(ReviewDifySetting).values(is_active=False))
        db.add(setting)
        db.flush()
        db.refresh(setting)
        return setting
