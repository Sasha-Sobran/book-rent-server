from datetime import datetime
from sqlmodel import Session

from app.models.rent import Rent
from app.penalties.utils import compute_overdue_days
from app.common.rent_utils import calculate_overdue_penalty
from app.common.constants import RentStatusNames


def calculate_rent_amounts(session: Session, rent: Rent) -> dict:
    if rent.return_date is not None:
        return {
            "days_in_use": 0,
            "overdue_days": 0,
            "planned_days": 0,
            "daily_rent_rate": 0.0,
            "actual_rent_amount": rent.rent_price,
            "overdue_penalty": 0.0,
            "total_amount": rent.rent_price,
        }

    now_date = datetime.utcnow().date()
    rent_date = rent.rent_date.date()
    expected_return_date = rent.expected_return_date.date()

    days_in_use = max((now_date - rent_date).days, 1)
    planned_days = max((expected_return_date - rent_date).days, 1)
    if planned_days <= 0:
        planned_days = 1

    daily_rent_rate = (
        rent.rent_price / planned_days if planned_days > 0 else rent.rent_price
    )
    actual_rent_amount = daily_rent_rate * days_in_use

    overdue_days = compute_overdue_days(rent)
    overdue_penalty = calculate_overdue_penalty(daily_rent_rate, overdue_days)

    total_amount = actual_rent_amount + overdue_penalty

    return {
        "days_in_use": days_in_use,
        "overdue_days": overdue_days,
        "planned_days": planned_days,
        "daily_rent_rate": daily_rent_rate,
        "actual_rent_amount": actual_rent_amount,
        "overdue_penalty": overdue_penalty,
        "total_amount": total_amount,
    }


def calculate_total_debt_for_rents(session: Session, rents: list[Rent]) -> float:
    total_debt = 0.0

    for rent in rents:
        session.refresh(rent, attribute_names=["status", "book"])

        if rent.return_date is None and rent.status.name in [
            RentStatusNames.ISSUED,
            RentStatusNames.OVERDUE,
            RentStatusNames.ACTIVE,
        ]:
            amounts = calculate_rent_amounts(session, rent)
            total_debt += amounts["total_amount"]

        if rent.return_date is None:
            from app.models.penalty import Penalty
            from sqlmodel import select

            penalties = session.exec(
                select(Penalty).where(Penalty.rent_id == rent.id)
            ).all()
            for penalty in penalties:
                total_debt += penalty.amount

    return round(total_debt, 2)
