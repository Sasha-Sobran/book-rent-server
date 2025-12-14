from pydantic import BaseModel, Field


class PenaltyCreate(BaseModel):
    rent_id: int = Field(gt=0)
    penalty_type: str
    days_overdue: int | None = Field(default=None, gt=0)
    damage_rate: float | None = Field(default=None, ge=0)
    manual_amount: float | None = Field(default=None, ge=0)


class PenaltyResponse(BaseModel):
    id: int
    rent_id: int
    penalty_type: str
    amount: float
