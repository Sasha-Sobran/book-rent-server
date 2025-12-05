from typing import Any, Type

from sqlalchemy import Result, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlmodel import SQLModel
from fastapi import HTTPException
from starlette import status


async def get_object_or_404(
    session: Session, model: SQLModel, **filters: Any
) -> SQLModel:
    obj = (await quick_select(session=session, model=model, filter_by=filters)).scalar()
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Object not found"
        )
    return obj


async def quick_select(
    session: Session, model: SQLModel, filters: Any = None, filter_by: dict = None
) -> Result:
    query = select(model)
    if filters is not None:
        query = query.where(*filters)
    if filter_by is not None:
        print(query)
        query = query.filter_by(**filter_by)
    return session.execute(query)


def create_object(session: Session, model: Type[SQLModel], **data: Any) -> SQLModel:
    try:
        obj = model(**data)
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj
    except IntegrityError as e:
        session.rollback()
        if (
            "unique constraint" in str(e.orig).lower()
            or "duplicate key" in str(e.orig).lower()
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Object with these values already exists",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(e)}",
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating object: {str(e)}",
        )
