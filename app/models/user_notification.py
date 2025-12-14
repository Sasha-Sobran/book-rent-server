from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel


class UserNotification(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    title: str
    message: str
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    book_id: int | None = Field(default=None, foreign_key="book.id")

    user: "User" = Relationship()
    book: "Book" = Relationship()
