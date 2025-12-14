from sqlalchemy.orm import Session
from sqlmodel import SQLModel


def save_and_refresh(session: Session, obj: SQLModel, *refresh_attrs: str) -> SQLModel:
    session.add(obj)
    session.commit()
    if refresh_attrs:
        session.refresh(obj, attribute_names=refresh_attrs)
    else:
        session.refresh(obj)
    return obj


def save_multiple_and_refresh(
    session: Session,
    *objs: SQLModel,
    refresh_attrs: list[tuple[SQLModel, tuple[str, ...]]] | None = None
) -> list[SQLModel]:
    for obj in objs:
        session.add(obj)
    session.commit()
    if refresh_attrs:
        for obj, attrs in refresh_attrs:
            session.refresh(obj, attribute_names=attrs)
    else:
        for obj in objs:
            session.refresh(obj)
    return list(objs)
