from typing import Type

from sqlmodel import Session, SQLModel, select

from app.common.db_utils import save_and_refresh


def get_or_create_by_name(
    session: Session,
    model: Type[SQLModel],
    name: str,
    name_field: str = "name",
) -> SQLModel:
    existing = session.exec(
        select(model).where(getattr(model, name_field) == name)
    ).first()
    if existing:
        return existing
    obj = model(**{name_field: name})
    return save_and_refresh(session, obj)
