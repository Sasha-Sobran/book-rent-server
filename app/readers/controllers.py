from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.reader import Reader
from app.models.user import User
from app.models.reader_category import ReaderCategory
from app.readers.schemas import CreateReaderRequest, ReaderResponse, UpdateReaderRequest


def get_all_readers(session: Session) -> list[ReaderResponse]:
    readers = session.exec(select(Reader)).all()
    return [_to_response(session, r) for r in readers]


def get_reader_by_id(session: Session, reader_id: int) -> ReaderResponse | None:
    reader = session.get(Reader, reader_id)
    if not reader:
        return None
    return _to_response(session, reader)


def search_readers(session: Session, query: str) -> list[ReaderResponse]:
    readers = session.exec(
        select(Reader).where(
            (Reader.name.ilike(f"%{query}%")) |
            (Reader.surname.ilike(f"%{query}%")) |
            (Reader.phone_number.ilike(f"%{query}%"))
        )
    ).all()
    return [_to_response(session, r) for r in readers]


def create_reader(session: Session, data: CreateReaderRequest) -> ReaderResponse:
    _validate_category(session, data.reader_category_id)
    _validate_user(session, data.user_id)
    reader = Reader(
        name=data.name,
        surname=data.surname,
        phone_number=data.phone_number,
        address=data.address,
        reader_category_id=data.reader_category_id,
        user_id=data.user_id,
    )
    session.add(reader)
    session.commit()
    session.refresh(reader)
    return _to_response(session, reader)


def update_reader(session: Session, reader_id: int, data: UpdateReaderRequest) -> ReaderResponse | None:
    reader = session.get(Reader, reader_id)
    if not reader:
        return None
    if data.name is not None:
        reader.name = data.name
    if data.surname is not None:
        reader.surname = data.surname
    if data.phone_number is not None:
        reader.phone_number = data.phone_number
    if data.address is not None:
        reader.address = data.address
    if data.reader_category_id is not None:
        _validate_category(session, data.reader_category_id)
        reader.reader_category_id = data.reader_category_id
    session.add(reader)
    session.commit()
    session.refresh(reader)
    return _to_response(session, reader)


def delete_reader(session: Session, reader_id: int) -> bool:
    reader = session.get(Reader, reader_id)
    if not reader:
        return False
    session.delete(reader)
    session.commit()
    return True


def _to_response(session: Session, reader: Reader) -> ReaderResponse:
    user_email = None
    if reader.user_id:
        user = session.get(User, reader.user_id)
        user_email = user.email if user else None
    
    category_name = None
    if reader.reader_category:
        category_name = reader.reader_category.name

    return ReaderResponse(
        id=reader.id,
        name=reader.name,
        surname=reader.surname,
        phone_number=reader.phone_number,
        address=reader.address,
        reader_category_id=reader.reader_category_id,
        reader_category_name=category_name,
        user_id=reader.user_id,
        user_email=user_email,
    )


def _validate_category(session: Session, category_id: int | None):
    if category_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reader category is required",
        )
    category = session.get(ReaderCategory, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader category not found",
        )


def _validate_user(session: Session, user_id: int | None):
    if user_id is None:
        return
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

