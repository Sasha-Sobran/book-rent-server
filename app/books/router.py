from fastapi import APIRouter, HTTPException, Query

from app.books.controllers import (
    create_book,
    delete_book,
    get_book,
    list_books,
    update_book,
)
from app.books.schemas import BookCreate, BookUpdate
from app.common.dependencies import LibrarianUserDep, SessionDep, UserDep
from app.models.librarian import Librarian
from sqlmodel import select

books_router = APIRouter(prefix="/books", tags=["books"])


@books_router.get("/")
async def list_books_route(
    session: SessionDep,
    user: UserDep,
    library_id: int | None = None,
    search: str | None = None,
    category_ids: list[int] | None = Query(default=None),
    genre_ids: list[int] | None = Query(default=None),
):
    parsed_category_ids = _parse_ids(category_ids)
    parsed_genre_ids = _parse_ids(genre_ids)

    return list_books(
        session,
        library_id=library_id,
        search=search,
        category_ids=parsed_category_ids,
        genre_ids=parsed_genre_ids,
    )


def _parse_ids(values: list[int] | list[str] | None) -> list[int] | None:
    if values is None:
        return None
    if len(values) == 1 and isinstance(values[0], str) and "," in values[0]:
        try:
            return [int(v) for v in values[0].split(",") if v.strip()]
        except ValueError:
            return None
    try:
        return [int(v) for v in values]
    except (TypeError, ValueError):
        return None


@books_router.get("/{book_id}/")
async def get_book_route(book_id: int, session: SessionDep, user: UserDep):
    book = get_book(session, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@books_router.post("/")
async def create_book_route(data: BookCreate, session: SessionDep, user: LibrarianUserDep):
    librarian_user_id = user["user_id"] if user.get("role_name") == "librarian" else None
    return create_book(session, data, librarian_user_id=librarian_user_id)


@books_router.put("/{book_id}/")
async def update_book_route(book_id: int, data: BookUpdate, session: SessionDep, user: LibrarianUserDep):
    book = update_book(session, book_id, data)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@books_router.delete("/{book_id}/")
async def delete_book_route(book_id: int, session: SessionDep, user: LibrarianUserDep):
    if not delete_book(session, book_id):
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book deleted"}

