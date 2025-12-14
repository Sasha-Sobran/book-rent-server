from datetime import datetime
from math import ceil
from sqlmodel import Session

from app.models.rent import Rent
from app.models.reader import Reader
from app.models.reader_category import ReaderCategory
from app.models.book import Book
from app.common.rent_utils import get_reader_discount, calculate_daily_rate


def compute_rent_days(rent: Rent) -> int:
    now_date = datetime.utcnow().date()
    rent_date = rent.rent_date.date()
    return max((now_date - rent_date).days, 1)


def compute_overdue_days(rent: Rent) -> int:
    return max((datetime.utcnow().date() - rent.expected_return_date.date()).days, 0)


def compute_daily_rent_rate(session: Session, rent: Rent) -> float:
    book = session.get(Book, rent.book_id)
    if not book:
        return 0.0
    reader = session.get(Reader, rent.reader_id)
    discount = get_reader_discount(session, reader) if reader else 0
    return calculate_daily_rate(book.price, discount)


def compute_overdue_penalty_no_discount(
    session: Session, rent: Rent, days_overdue: int
) -> float:
    book = session.get(Book, rent.book_id)
    if not book:
        return 0.0
    daily_rate = calculate_daily_rate(book.price, 0)
    return round(daily_rate * days_overdue, 2)
