from sqlmodel import Field, Relationship, SQLModel


class Reader(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="user.id")
    reader_category_id: int | None = Field(
        default=None, foreign_key="reader_category.id"
    )
    name: str
    surname: str
    phone_number: str | None = Field(default=None)
    address: str | None = Field(default=None)

    reader_category: "ReaderCategory" = Relationship(back_populates="readers")
    user: "User" = Relationship(back_populates="readers")
    rents: list["Rent"] = Relationship(back_populates="reader")
