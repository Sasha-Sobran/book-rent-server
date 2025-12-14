from fastapi import APIRouter

from app.common.dependencies import LibrarianUserDep, SessionDep
from app.penalties.schemas import PenaltyCreate, PenaltyResponse
from app.penalties.services import create_penalty_with_strategy

penalties_router = APIRouter(prefix="/penalties", tags=["penalties"])


@penalties_router.post("/", response_model=PenaltyResponse)
async def create_penalty_route(
    data: PenaltyCreate, session: SessionDep, user: LibrarianUserDep
):
    penalty = create_penalty_with_strategy(
        session=session,
        rent_id=data.rent_id,
        penalty_type_name=data.penalty_type,
        days_overdue=data.days_overdue,
        damage_rate=data.damage_rate,
        manual_amount=data.manual_amount,
    )
    return PenaltyResponse(
        id=penalty.id,
        rent_id=penalty.rent_id,
        penalty_type=penalty.penalty_type.name,
        amount=penalty.amount,
    )
