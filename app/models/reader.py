from sqlmodel import Field, Relationship, SQLModel

class Reader(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    reader_category_id: int = Field(foreign_key="reader_category.id")
    address: int

    reader_category: "ReaderCategory" = Relationship(back_populates="readers")
    user: "User" = Relationship(back_populates="readers")
    rents: list["Rent"] = Relationship(back_populates="reader")