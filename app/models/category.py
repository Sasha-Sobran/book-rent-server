from sqlmodel import Relationship, SQLModel, Field

from app.models.book import BookCategory


class Category(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    books: list["Book"] = Relationship(
        back_populates="categories", link_model=BookCategory
    )
