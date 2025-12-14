from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.book import Book
from app.models.librarian import Librarian
from app.models.rent import Rent


def check_book_library_access(session: Session, book: Book, librarian: Librarian):
    if book.library_id != librarian.library_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage books from your library",
        )


def check_rent_ownership(rent: Rent, librarian_id: int, action: str = "manage"):
    if rent.librarian_id != librarian_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You can only {action} rents you created",
        )


def check_rent_reader_access(session: Session, rent: Rent, user_id: int):
    session.refresh(rent, attribute_names=["reader"])
    if not rent.reader or rent.reader.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage your own rents",
        )
