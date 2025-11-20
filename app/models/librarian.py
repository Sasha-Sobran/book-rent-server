from sqlmodel import Field, Relationship, SQLModel


class Librarian(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    library_id: int = Field(foreign_key="library.id")

    user: "User" = Relationship(back_populates="librarians")
    library: "Library" = Relationship(back_populates="librarians")
    rents: list["Rent"] = Relationship(back_populates="librarian")
