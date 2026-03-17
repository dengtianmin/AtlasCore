from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.review_rubric_setting import ReviewRubricSetting


class ReviewRubricSettingRepository:
    def get_active(self, db: Session) -> ReviewRubricSetting | None:
        stmt = select(ReviewRubricSetting).where(ReviewRubricSetting.is_active.is_(True)).order_by(ReviewRubricSetting.updated_at.desc())
        return db.execute(stmt).scalar_one_or_none()

    def replace_active(self, db: Session, *, setting: ReviewRubricSetting) -> ReviewRubricSetting:
        db.execute(update(ReviewRubricSetting).values(is_active=False))
        db.add(setting)
        db.flush()
        db.refresh(setting)
        return setting
