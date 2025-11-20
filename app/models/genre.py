from sqlmodel import Field, Relationship, SQLModel

from app.models.book import BookGenre

class Genre(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    books: list["Book"] = Relationship(back_populates="genres", link_model=BookGenre)
    