from sqlmodel import Relationship, SQLModel, Field


class City(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    libraries: list["Library"] = Relationship(back_populates="city")
