from sqlmodel import Field, Relationship, SQLModel


class RentStatus(SQLModel, table=True):
    __tablename__ = "rent_status"

    id: int = Field(default=None, primary_key=True)
    name: str

    rents: list["Rent"] = Relationship(back_populates="status")
