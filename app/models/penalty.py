from sqlmodel import Field, Relationship, SQLModel


class Penalty(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    rent_id: int = Field(foreign_key="rent.id")
    penalty_type_id: int = Field(foreign_key="penalty_type.id")
    amount: float

    rent: "Rent" = Relationship(back_populates="penalties")
    penalty_type: "PenaltyType" = Relationship(back_populates="penalties")
