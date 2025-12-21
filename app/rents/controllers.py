from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from app.common.db_utils import save_and_refresh, save_multiple_and_refresh
from app.models.book import Book
from app.models.librarian import Librarian
from app.models.penalty import Penalty
from app.models.penalty_type import PenaltyType
from app.models.user import User
from app.models.reader import Reader
from app.models.reader_category import ReaderCategory
from app.models.rent import Rent
from app.models.rent_status import RentStatus
from app.rents.schemas import RentCreate, RentResponse
from app.penalties.services import create_penalty_with_strategy
from app.penalties.utils import compute_daily_rent_rate, compute_rent_days

from app.common.rent_utils import (
    DAILY_RATE_PERCENT,
    get_reader_discount,
    calculate_daily_rate,
)
from app.common.constants import RentConstants, RentStatusNames
from app.common.validators import get_or_404
from app.common.permissions import (
    check_book_library_access,
    check_rent_ownership,
    check_rent_reader_access,
)
from app.common.librarian_utils import (
    get_librarian_by_user_id,
    require_librarian_by_user_id,
)
from app.common.utils import get_or_create_by_name

LOAN_DAYS_DEFAULT = RentConstants.LOAN_DAYS_DEFAULT


def list_rents(
    session: Session,
    librarian_user_id: int | None = None,
    reader_id: int | None = None,
    reader_user_id: int | None = None,
    status_name: str | None = None,
    library_id: int | None = None,
) -> list[RentResponse]:
    query = select(Rent).options(
        selectinload(Rent.book),
        selectinload(Rent.reader),
        selectinload(Rent.status),
        selectinload(Rent.penalties).selectinload(Penalty.penalty_type),
    )
    if reader_id is not None:
        query = query.where(Rent.reader_id == reader_id)
    if reader_user_id is not None:
        query = query.join(Reader).where(Reader.user_id == reader_user_id)
    if library_id is not None:
        query = query.join(Book).where(Book.library_id == library_id)
    librarian = (
        get_librarian_by_user_id(session, librarian_user_id)
        if librarian_user_id
        else None
    )
    if librarian:
        query = query.where(Rent.librarian_id == librarian.id)

    if status_name:
        query = query.join(RentStatus).where(RentStatus.name == status_name)
    rents = session.exec(query).all()
    return [_to_response(r) for r in rents]


def get_rent(session: Session, rent_id: int) -> RentResponse | None:
    rent = session.get(Rent, rent_id)
    if not rent:
        return None
    session.refresh(
        rent,
        attribute_names=[
            "book",
            "reader",
            "status",
            "penalties",
            "penalties.penalty_type",
        ],
    )
    rent.penalties
    return _to_response(rent)


def create_rent(
    session: Session, data: RentCreate, librarian_user_id: int | None = None
) -> RentResponse:
    book = get_or_404(session, Book, data.book_id, "Book")
    if book.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book is not available for rent",
        )
    
    librarian = None
    if librarian_user_id:
        librarian = require_librarian_by_user_id(session, librarian_user_id)
        check_book_library_access(session, book, librarian)
    else:
        from app.models.library import Library
        from app.models.librarian import Librarian
        library = session.get(Library, book.library_id)
        if library:
            librarian_result = session.exec(
                select(Librarian).where(Librarian.library_id == library.id).limit(1)
            ).first()
            if not librarian_result:
                librarian_result = session.exec(select(Librarian).limit(1)).first()
                if not librarian_result:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No librarians available in the system",
                    )
            librarian = librarian_result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Library not found for this book",
            )

    reader = get_or_404(session, Reader, data.reader_id, "Reader")

    category = _get_reader_category(session, reader)

    loan_days = data.loan_days or LOAN_DAYS_DEFAULT
    if loan_days <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Loan days must be positive",
        )

    discount = max(category.discount_percentage or 0, 0)
    daily_rate = calculate_daily_rate(book.price, discount)
    rent_price = max(daily_rate * loan_days, 0)
    deposit_price = max(int(round(book.price)), 0)
    expected_return_date = datetime.utcnow() + timedelta(days=loan_days)
    status_active = _get_or_create_status(session, name=RentStatusNames.ACTIVE)

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
    save_multiple_and_refresh(
        session, book, rent, refresh_attrs=[(rent, ("book", "reader", "status"))]
    )
    return _to_response(rent)


def create_rent_order(
    session: Session, book_id: int, loan_days: int | None, user_id: int
) -> RentResponse:
    book = get_or_404(session, Book, book_id, "Book")
    reader = session.exec(select(Reader).where(Reader.user_id == user_id)).first()
    if not reader:
        user = get_or_404(session, User, user_id, "User")
        reader = Reader(
            user_id=user_id,
            name=user.name,
            surname=user.surname,
            phone_number=user.phone_number,
        )
        save_and_refresh(session, reader)
    
    librarian = session.exec(
        select(Librarian).where(Librarian.library_id == book.library_id)
    ).first()
    
    if not librarian:
        librarian = session.exec(select(Librarian).limit(1)).first()
        if not librarian:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No librarians available in the system",
            )

    loan_days_val = loan_days or LOAN_DAYS_DEFAULT
    if loan_days_val <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Loan days must be positive"
        )
    discount = get_reader_discount(session, reader)
    daily_rate = calculate_daily_rate(book.price, discount)
    rent_price = max(daily_rate * loan_days_val, 0)
    deposit_price = max(int(round(book.price)), 0)
    expected_return_date = datetime.utcnow() + timedelta(days=loan_days_val)
    status_pending = _get_or_create_status(session, name=RentStatusNames.PENDING)

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
    save_and_refresh(session, rent, "book", "reader", "status")
    return _to_response(rent)


def return_rent(
    session: Session, rent_id: int, librarian_user_id: int | None = None
) -> RentResponse | None:
    librarian = (
        require_librarian_by_user_id(session, librarian_user_id)
        if librarian_user_id
        else None
    )
    rent = session.get(Rent, rent_id)
    if not rent:
        return None
    if librarian:
        check_rent_ownership(rent, librarian.id, "close")
    if rent.return_date:
        session.refresh(rent, attribute_names=["book", "reader", "status"])
        return _to_response(rent)

    actual_days = compute_rent_days(rent)
    daily_rate = compute_daily_rent_rate(session, rent)
    rent.rent_price = max(round(daily_rate * actual_days, 2), 0)

    from app.penalties.utils import compute_overdue_days

    days_overdue = compute_overdue_days(rent)
    if days_overdue > 0:
        existing_overdue = session.exec(
            select(Penalty)
            .join(PenaltyType)
            .where(Penalty.rent_id == rent.id, PenaltyType.name == "overdue")
        ).first()
        if not existing_overdue:
            create_penalty_with_strategy(
                session=session,
                rent_id=rent.id,
                penalty_type_name="overdue",
                days_overdue=days_overdue,
            )

    rent.return_date = datetime.utcnow()
    rent.status_id = _get_or_create_status(session, name=RentStatusNames.RETURNED).id

    book = session.get(Book, rent.book_id)
    was_unavailable = False
    if book:
        was_unavailable = book.quantity == 0
        book.quantity += 1
        session.add(book)

    save_and_refresh(session, rent, "book", "reader", "status")

    if was_unavailable and book:
        from app.books.observer import BookAvailabilityObserver

        BookAvailabilityObserver.notify_subscribers(session, book.id)

    return _to_response(rent)


def issue_rent(
    session: Session, rent_id: int, librarian_user_id: int | None = None
) -> RentResponse | None:
    librarian = (
        require_librarian_by_user_id(session, librarian_user_id)
        if librarian_user_id
        else None
    )
    rent = session.get(Rent, rent_id)
    if not rent:
        return None
    if librarian:
        check_rent_ownership(rent, librarian.id, "issue")
    if rent.status and rent.status.name != RentStatusNames.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending rents can be issued",
        )
    rent.status_id = _get_or_create_status(session, name=RentStatusNames.ACTIVE).id
    rent.rent_date = datetime.utcnow()

    book = session.get(Book, rent.book_id)
    if book:
        if book.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Book is not available for rent",
            )
        book.quantity -= 1
        session.add(book)

    save_and_refresh(session, rent, "book", "reader", "status")
    return _to_response(rent)


def decline_rent(
    session: Session, rent_id: int, librarian_user_id: int | None = None
) -> RentResponse | None:
    librarian = (
        require_librarian_by_user_id(session, librarian_user_id)
        if librarian_user_id
        else None
    )
    rent = session.get(Rent, rent_id)
    if not rent:
        return None
    if librarian:
        check_rent_ownership(rent, librarian.id, "decline")
    if rent.status and rent.status.name != RentStatusNames.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending rents can be declined",
        )
    rent.status_id = _get_or_create_status(session, name=RentStatusNames.DECLINED).id
    save_and_refresh(session, rent, "book", "reader", "status")
    return _to_response(rent)


def cancel_rent(session: Session, rent_id: int, user_id: int) -> RentResponse | None:
    rent = session.get(Rent, rent_id)
    if not rent:
        return None
    session.refresh(rent, attribute_names=["reader", "status"])
    check_rent_reader_access(session, rent, user_id)
    if rent.status and rent.status.name != RentStatusNames.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending rents can be cancelled",
        )
    rent.status_id = _get_or_create_status(session, name=RentStatusNames.CANCELLED).id
    save_and_refresh(session, rent, "book", "reader", "status")
    return _to_response(rent)


def _get_or_create_status(session: Session, name: str) -> RentStatus:
    return get_or_create_by_name(session, RentStatus, name)


def _get_reader_category(session: Session, reader: Reader) -> ReaderCategory:
    if reader.reader_category:
        return reader.reader_category
    if reader.reader_category_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reader does not have a category assigned",
        )
    category = get_or_404(
        session, ReaderCategory, reader.reader_category_id, "Reader category"
    )
    return category


def _to_response(rent: Rent) -> RentResponse:
    reader_name = ""
    if rent.reader:
        reader_name = f"{rent.reader.name} {rent.reader.surname}".strip()

    status_name = rent.status.name if rent.status else ""
    penalties_total = sum(p.amount for p in rent.penalties or [])
    total_amount = rent.rent_price + penalties_total

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
        penalties_amount=penalties_total,
        total_amount=total_amount,
    )
