from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel


class BookNotification(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    book_id: int = Field(foreign_key="book.id")
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    book: "Book" = Relationship()
    user: "User" = Relationship()
