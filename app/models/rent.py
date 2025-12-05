from typing import Optional
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime


class Rent(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    book_id: int = Field(foreign_key="book.id")
    reader_id: int = Field(foreign_key="reader.id")
    rent_date: datetime
    return_date: Optional[datetime]
    expected_return_date: datetime
    rent_price: float
    status_id: int = Field(foreign_key="rent_status.id")
    librarian_id: int = Field(foreign_key="librarian.id")
    deposit_price: int

    penalties: list["Penalty"] = Relationship(back_populates="rent")
    reader: "Reader" = Relationship(back_populates="rents")
    librarian: "Librarian" = Relationship(back_populates="rents")
    book: "Book" = Relationship(back_populates="rents")
    status: "RentStatus" = Relationship(back_populates="rents")
