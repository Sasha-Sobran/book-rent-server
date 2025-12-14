from typing import Type

from fastapi import HTTPException, status
from sqlmodel import Session, SQLModel


def get_or_404(
    session: Session,
    model: Type[SQLModel],
    entity_id: int,
    entity_name: str | None = None,
) -> SQLModel:
    entity = session.get(model, entity_id)
    if not entity:
        name = entity_name or model.__name__
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{name} not found",
        )
    return entity
