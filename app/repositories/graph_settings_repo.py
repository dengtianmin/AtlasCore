from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.graph_model_setting import GraphModelSetting
from app.models.graph_prompt_setting import GraphPromptSetting


class GraphPromptSettingRepository:
    def get_active(self, db: Session) -> GraphPromptSetting | None:
        stmt = select(GraphPromptSetting).where(GraphPromptSetting.is_active.is_(True)).order_by(GraphPromptSetting.updated_at.desc())
        return db.execute(stmt).scalar_one_or_none()

    def replace_active(self, db: Session, *, setting: GraphPromptSetting) -> GraphPromptSetting:
        db.execute(update(GraphPromptSetting).values(is_active=False))
        db.add(setting)
        db.flush()
        db.refresh(setting)
        return setting


class GraphModelSettingRepository:
    def get_active(self, db: Session) -> GraphModelSetting | None:
        stmt = select(GraphModelSetting).where(GraphModelSetting.is_active.is_(True)).order_by(GraphModelSetting.updated_at.desc())
        return db.execute(stmt).scalar_one_or_none()

    def replace_active(self, db: Session, *, setting: GraphModelSetting) -> GraphModelSetting:
        db.execute(update(GraphModelSetting).values(is_active=False))
        db.add(setting)
        db.flush()
        db.refresh(setting)
        return setting
