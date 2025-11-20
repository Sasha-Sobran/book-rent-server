from sqlmodel import Field, Relationship, SQLModel

class Library(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    city_id: int = Field(foreign_key="city.id")
    address: str
    phone_number: str

    books: list["Book"] = Relationship(back_populates="library")
    librarians: list["Librarian"] = Relationship(back_populates="library")
    city: "City" = Relationship(back_populates="libraries")