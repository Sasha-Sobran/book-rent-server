from sqlmodel import Field, Relationship, SQLModel

class PenaltyType(SQLModel, table=True):
    __tablename__ = "penalty_type"

    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    penalties: list["Penalty"] = Relationship(back_populates="penalty_type")
    