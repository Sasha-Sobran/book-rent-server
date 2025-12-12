from datetime import datetime

from pydantic import BaseModel, Field


class RentCreate(BaseModel):
    book_id: int = Field(gt=0)
    reader_id: int = Field(gt=0)
    loan_days: int | None = Field(default=None, gt=0)


class RentOrderCreate(BaseModel):
    book_id: int = Field(gt=0)
    loan_days: int | None = Field(default=None, gt=0)


class RentResponse(BaseModel):
    id: int
    book_id: int
    book_title: str
    reader_id: int
    reader_name: str
    rent_date: datetime
    expected_return_date: datetime
    return_date: datetime | None
    rent_price: float
    deposit_price: int
    status: str
    librarian_id: int


