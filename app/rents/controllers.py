from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.book import Book
from app.models.librarian import Librarian
from app.models.user import User
from app.models.reader import Reader
from app.models.reader_category import ReaderCategory
from app.models.rent import Rent
from app.models.rent_status import RentStatus
from app.rents.schemas import RentCreate, RentResponse

LOAN_DAYS_DEFAULT = 14
DAILY_RATE_PERCENT = 0.02


def list_rents(
    session: Session,
    librarian_user_id: int | None = None,
    reader_id: int | None = None,
    reader_user_id: int | None = None,
    status_name: str | None = None,
) -> list[RentResponse]:
    query = select(Rent)    
    if reader_id is not None:
        query = query.where(Rent.reader_id == reader_id)
    if reader_user_id is not None:
        query = query.join(Reader).where(Reader.user_id == reader_user_id)
    librarian = _get_librarian(session, librarian_user_id) if librarian_user_id else None
    if librarian:
        query = query.where(Rent.librarian_id == librarian.id)

    if status_name:
        query = query.join(RentStatus).where(RentStatus.name == status_name)
    rents = session.exec(query).all()
    for rent in rents:
        session.refresh(rent, attribute_names=["book", "reader", "status"])
    return [_to_response(r) for r in rents]


def get_rent(session: Session, rent_id: int) -> RentResponse | None:
    rent = session.get(Rent, rent_id)
    if not rent:
        return None
    session.refresh(rent, attribute_names=["book", "reader", "status"])
    return _to_response(rent)


def create_rent(
    session: Session, data: RentCreate, librarian_user_id: int
) -> RentResponse:
    librarian = _require_librarian(session, librarian_user_id)
    book = session.get(Book, data.book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    if book.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book is not available for rent",
        )
    if book.library_id != librarian.library_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only rent books from your library",
        )

    reader = session.get(Reader, data.reader_id)
    if not reader:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reader not found")

    category = _get_reader_category(session, reader)

    loan_days = data.loan_days or LOAN_DAYS_DEFAULT
    if loan_days <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Loan days must be positive",
        )

    discount = max(category.discount_percentage or 0, 0)
    daily_rate = max(book.price * DAILY_RATE_PERCENT, 0)
    rent_price = max(daily_rate * loan_days * (1 - discount / 100), 0)
    deposit_price = max(int(round(book.price)), 0)
    expected_return_date = datetime.utcnow() + timedelta(days=loan_days)
    status_active = _get_or_create_status(session, name="active")

    rent = Rent(
        book_id=book.id,
        reader_id=reader.id,
        rent_date=datetime.utcnow(),
        expected_return_date=expected_return_date,
        rent_price=rent_price,
        status_id=status_active.id,
        librarian_id=librarian.id,
        deposit_price=deposit_price,
    )

    book.quantity -= 1
    session.add(book)
    session.add(rent)
    session.commit()
    session.refresh(rent)
    session.refresh(rent, attribute_names=["book", "reader", "status"])
    return _to_response(rent)


def create_rent_order(session: Session, book_id: int, loan_days: int | None, user_id: int) -> RentResponse:
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    reader = session.exec(select(Reader).where(Reader.user_id == user_id)).first()
    if not reader:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        reader = Reader(
            user_id=user_id,
            name=user.name,
            surname=user.surname,
            phone_number=user.phone_number,
        )
        session.add(reader)
        session.commit()
    librarian = session.exec(select(Librarian).where(Librarian.library_id == book.library_id)).first()
    if not librarian:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No librarian for this library",
        )

    loan_days_val = loan_days or LOAN_DAYS_DEFAULT
    if loan_days_val <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Loan days must be positive")
    discount = _reader_discount(session, reader)
    daily_rate = max(book.price * DAILY_RATE_PERCENT, 0)
    rent_price = max(daily_rate * loan_days_val * (1 - discount / 100), 0)
    deposit_price = max(int(round(book.price)), 0)
    expected_return_date = datetime.utcnow() + timedelta(days=loan_days_val)
    status_pending = _get_or_create_status(session, name="pending")

    rent = Rent(
        book_id=book.id,
        reader_id=reader.id,
        rent_date=datetime.utcnow(),
        expected_return_date=expected_return_date,
        rent_price=rent_price,
        status_id=status_pending.id,
        librarian_id=librarian.id,
        deposit_price=deposit_price,
    )
    session.add(rent)
    session.commit()
    session.refresh(rent, attribute_names=["book", "reader", "status"])
    return _to_response(rent)


def return_rent(session: Session, rent_id: int, librarian_user_id: int) -> RentResponse | None:
    librarian = _require_librarian(session, librarian_user_id)
    rent = session.get(Rent, rent_id)
    if not rent:
        return None
    if rent.librarian_id != librarian.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only close rents you created",
        )
    if rent.return_date:
        session.refresh(rent, attribute_names=["book", "reader", "status"])
        return _to_response(rent)

    rent.return_date = datetime.utcnow()
    rent.status_id = _get_or_create_status(session, name="returned").id

    book = session.get(Book, rent.book_id)
    if book:
        book.quantity += 1
        session.add(book)

    session.add(rent)
    session.commit()
    session.refresh(rent, attribute_names=["book", "reader", "status"])
    return _to_response(rent)


def issue_rent(session: Session, rent_id: int, librarian_user_id: int) -> RentResponse | None:
    librarian = _require_librarian(session, librarian_user_id)
    rent = session.get(Rent, rent_id)
    if not rent:
        return None
    if rent.librarian_id != librarian.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only issue rents you created",
        )
    if rent.status and rent.status.name != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending rents can be issued",
        )
    rent.status_id = _get_or_create_status(session, name="active").id
    rent.rent_date = datetime.utcnow()

    book = session.get(Book, rent.book_id)
    if book:
        if book.quantity <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book is not available for rent")
        book.quantity -= 1
        session.add(book)

    session.add(rent)
    session.commit()
    session.refresh(rent, attribute_names=["book", "reader", "status"])
    return _to_response(rent)


def decline_rent(session: Session, rent_id: int, librarian_user_id: int) -> RentResponse | None:
    librarian = _require_librarian(session, librarian_user_id)
    rent = session.get(Rent, rent_id)
    if not rent:
        return None
    if rent.librarian_id != librarian.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only decline rents you created",
        )
    if rent.status and rent.status.name != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending rents can be declined",
        )
    rent.status_id = _get_or_create_status(session, name="declined").id
    rent.cancelled_at = datetime.utcnow()
    session.add(rent)
    session.commit()
    session.refresh(rent, attribute_names=["book", "reader", "status"])
    return _to_response(rent)


def cancel_rent(session: Session, rent_id: int, user_id: int) -> RentResponse | None:
    rent = session.get(Rent, rent_id)
    if not rent:
        return None
    session.refresh(rent, attribute_names=["reader", "status"])
    if not rent.reader or rent.reader.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own rents",
        )
    if rent.status and rent.status.name != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending rents can be cancelled",
        )
    rent.status_id = _get_or_create_status(session, name="cancelled").id
    rent.cancelled_at = datetime.utcnow()
    session.add(rent)
    session.commit()
    session.refresh(rent, attribute_names=["book", "reader", "status"])
    return _to_response(rent)


def _get_or_create_status(session: Session, name: str) -> RentStatus:
    existing = session.exec(select(RentStatus).where(RentStatus.name == name)).first()
    if existing:
        return existing
    status_obj = RentStatus(name=name)
    session.add(status_obj)
    session.commit()
    session.refresh(status_obj)
    return status_obj


def _get_reader_category(session: Session, reader: Reader) -> ReaderCategory:
    if reader.reader_category:
        return reader.reader_category
    if reader.reader_category_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reader does not have a category assigned",
        )
    category = session.get(ReaderCategory, reader.reader_category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reader category not found",
        )
    return category


def _reader_discount(session: Session, reader: Reader) -> int:
    if reader.reader_category:
        return max(reader.reader_category.discount_percentage or 0, 0)
    if reader.reader_category_id is None:
        return 0
    category = session.get(ReaderCategory, reader.reader_category_id)
    if not category:
        return 0
    return max(category.discount_percentage or 0, 0)


def _get_librarian(session: Session, user_id: int | None) -> Librarian | None:
    if user_id is None:
        return None
    result = session.exec(select(Librarian).where(Librarian.user_id == user_id))
    return result.first()


def _require_librarian(session: Session, user_id: int) -> Librarian:
    librarian = _get_librarian(session, user_id)
    if not librarian:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Current user is not linked to a librarian profile",
        )
    return librarian


def _to_response(rent: Rent) -> RentResponse:
    reader_name = ""
    if rent.reader:
        reader_name = f"{rent.reader.name} {rent.reader.surname}".strip()

    status_name = rent.status.name if rent.status else ""

    return RentResponse(
        id=rent.id,
        book_id=rent.book_id,
        book_title=rent.book.title if rent.book else "",
        reader_id=rent.reader_id,
        reader_name=reader_name,
        rent_date=rent.rent_date,
        expected_return_date=rent.expected_return_date,
        return_date=rent.return_date,
        rent_price=rent.rent_price,
        deposit_price=rent.deposit_price,
        status=status_name,
        librarian_id=rent.librarian_id,
    )


