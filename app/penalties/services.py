from typing import Protocol

from fastapi import HTTPException, status
from sqlmodel import Session

from app.common.db_utils import save_and_refresh
from app.common.rent_utils import (
    calculate_daily_rate,
    calculate_overdue_penalty,
    get_reader_discount,
)
from app.common.validators import get_or_404
from app.common.utils import get_or_create_by_name
from app.models.book import Book
from app.models.penalty import Penalty
from app.models.penalty_type import PenaltyType
from app.models.reader import Reader
from app.models.rent import Rent

DEFAULT_DAMAGE_RATE = 0.3


class PenaltyStrategy(Protocol):
    def calculate(self, session: Session, rent: Rent, **kwargs) -> float: ...


def _ensure_penalty_type(session: Session, name: str) -> PenaltyType:
    return get_or_create_by_name(session, PenaltyType, name)


class OverduePenaltyStrategy:
    def calculate(self, session: Session, rent: Rent, **kwargs) -> float:
        days_overdue: int | None = kwargs.get("days_overdue")
        if not days_overdue or days_overdue <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="days_overdue must be positive for overdue penalties",
            )
        book = session.get(Book, rent.book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
            )
        reader = session.get(Reader, rent.reader_id)
        discount = get_reader_discount(session, reader) if reader else 0
        daily_rate = calculate_daily_rate(book.price, discount)
        return calculate_overdue_penalty(daily_rate, days_overdue)


class DamagePenaltyStrategy:
    def calculate(self, session: Session, rent: Rent, **kwargs) -> float:
        rate: float = kwargs.get("damage_rate") or DEFAULT_DAMAGE_RATE
        if rate < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="damage_rate must be non-negative",
            )
        book = get_or_404(session, Book, rent.book_id, "Book")
        amount = max(book.price * rate, 0)
        return round(amount, 2)


class LostPenaltyStrategy:
    def calculate(self, session: Session, rent: Rent, **kwargs) -> float:
        book = get_or_404(session, Book, rent.book_id, "Book")
        return max(round(book.price, 2), 0)


class ManualPenaltyStrategy:
    def calculate(self, session: Session, rent: Rent, **kwargs) -> float:
        amount = kwargs.get("manual_amount")
        if amount is None or amount < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="manual_amount must be provided and non-negative",
            )
        return round(float(amount), 2)


STRATEGY_MAP: dict[str, PenaltyStrategy] = {
    "overdue": OverduePenaltyStrategy(),
    "damage": DamagePenaltyStrategy(),
    "lost": LostPenaltyStrategy(),
    "manual": ManualPenaltyStrategy(),
}


def create_penalty_with_strategy(
    session: Session,
    rent_id: int,
    penalty_type_name: str,
    **kwargs,
) -> Penalty:
    rent = get_or_404(session, Rent, rent_id, "Rent")

    name = penalty_type_name.lower()
    strategy = STRATEGY_MAP.get(name)
    if strategy is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported penalty type '{penalty_type_name}'",
        )

    amount = strategy.calculate(session, rent, **kwargs)
    penalty_type = _ensure_penalty_type(session, name)

    penalty = Penalty(
        rent_id=rent.id,
        penalty_type_id=penalty_type.id,
        amount=amount,
    )
    return save_and_refresh(session, penalty)
