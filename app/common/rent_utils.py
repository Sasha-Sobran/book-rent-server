from sqlmodel import Session

from app.models.book import Book
from app.models.reader import Reader
from app.models.reader_category import ReaderCategory

DAILY_RATE_PERCENT = 0.02
OVERDUE_PENALTY_MULTIPLIER = 1.2


def get_reader_discount(session: Session, reader: Reader) -> int:
    if reader.reader_category_id is None:
        return 0

    category = session.get(ReaderCategory, reader.reader_category_id)
    if not category or category.discount_percentage is None:
        return 0

    return max(category.discount_percentage, 0)


def calculate_daily_rate(book_price: float, discount_percentage: int = 0) -> float:
    daily_rate = max(book_price * DAILY_RATE_PERCENT, 0)
    return daily_rate * (1 - discount_percentage / 100)


def calculate_overdue_penalty(daily_rate: float, days_overdue: int) -> float:
    if days_overdue <= 0:
        return 0.0
    return round(daily_rate * OVERDUE_PENALTY_MULTIPLIER * days_overdue, 2)
