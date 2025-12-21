import os
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.books.controllers import (
    create_book,
    delete_book,
    get_book,
    get_popular_books,
    list_books,
    update_book,
)
from app.books.notifications_controller import (
    get_subscription_status,
    subscribe,
    unsubscribe,
)
from app.books.schemas import BookCreate, BookUpdate
from app.common.dependencies import RootUserDep, LibrarianUserDep, SessionDep, UserDep
from app.common.permissions import check_book_library_access
from app.common.librarian_utils import get_librarian_from_user_dict
from app.models.book import Book
from app.event_log.decorators import audit_log

books_router = APIRouter(prefix="/books", tags=["books"])


@books_router.get("/")
async def list_books_route(
    session: SessionDep,
    user: UserDep,
    library_id: int | None = None,
    search: str | None = None,
    category_ids: str | None = Query(default=None),
    genre_ids: str | None = Query(default=None),
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


def _parse_ids(value: str | None) -> list[int] | None:
    if value is None or not value.strip():
        return None
    try:
        if isinstance(value, str):
            return [int(v.strip()) for v in value.split(",") if v.strip()]
        return None
    except (ValueError, TypeError):
        return None


@books_router.get("/popular/")
async def get_popular_books_route(
    session: SessionDep,
    user: UserDep,
    library_id: int | None = None,
    limit: int = 8,
):
    return get_popular_books(session, library_id=library_id, limit=limit)


@books_router.get("/{book_id}/")
async def get_book_route(book_id: int, session: SessionDep, user: UserDep):
    book = get_book(session, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@books_router.post("/")
@audit_log(
    action_type="create",
    entity_type="book",
    get_entity_id=lambda result, *args, **kwargs: result.id if result else None,
    get_description=lambda result, *args, **kwargs: (
        f"Створено книгу '{result.title}'" if result else None
    ),
    get_new_values=lambda result, *args, **kwargs: (
        {
            "title": result.title,
            "author": result.author,
            "price": result.price,
            "publish_year": result.publish_year,
            "quantity": result.quantity,
        }
        if result
        else None
    ),
)
async def create_book_route(
    data: BookCreate, session: SessionDep, user: LibrarianUserDep
):
    return create_book(session, data, librarian_user_id=user["user_id"])


@books_router.put("/{book_id}/")
@audit_log(
    action_type="update",
    entity_type="book",
    get_entity_id=lambda result, book_id, *args, **kwargs: (
        result.id if result else book_id
    ),
    get_description=lambda result, book_id, *args, **kwargs: (
        f"Оновлено книгу '{result.title}'"
        if result
        else f"Оновлено книгу (ID: {book_id})"
    ),
    get_old_values=lambda result, session, book_id, *args, **kwargs: (
        {
            "title": old_book.title,
            "author": old_book.author,
            "price": old_book.price,
            "quantity": old_book.quantity,
        }
        if session and (old_book := session.get(Book, book_id))
        else None
    ),
    get_new_values=lambda result, *args, **kwargs: (
        {
            "title": result.title,
            "author": result.author,
            "price": result.price,
            "quantity": result.quantity,
        }
        if result
        else None
    ),
)
async def update_book_route(
    book_id: int, data: BookUpdate, session: SessionDep, user: LibrarianUserDep
):
    librarian = get_librarian_from_user_dict(session, user)
    if librarian:
        book = session.get(Book, book_id)
        if book:
            check_book_library_access(session, book, librarian)

    book = update_book(session, book_id, data)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@books_router.delete("/{book_id}/")
@audit_log(
    action_type="delete",
    entity_type="book",
    get_entity_id=lambda result, book_id, *args, **kwargs: book_id,
    get_description=lambda result, session, book_id, *args, **kwargs: (
        f"Видалено книгу '{book.title}'"
        if session and (book := session.get(Book, book_id))
        else f"Видалено книгу (ID: {book_id})"
    ),
    get_old_values=lambda result, session, book_id, *args, **kwargs: (
        {
            "title": book.title,
            "author": book.author,
            "price": book.price,
        }
        if session and (book := session.get(Book, book_id))
        else None
    ),
)
async def delete_book_route(book_id: int, session: SessionDep, user: LibrarianUserDep):
    librarian = get_librarian_from_user_dict(session, user)
    if librarian:
        book = session.get(Book, book_id)
        if book:
            check_book_library_access(session, book, librarian)

    if not delete_book(session, book_id):
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book deleted"}


BASE_DIR = Path(__file__).parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads" / "books"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024


@books_router.post("/{book_id}/upload-image")
@audit_log(
    action_type="update",
    entity_type="book",
    get_entity_id=lambda result, book_id, *args, **kwargs: book_id,
    get_description=lambda result, book_id, *args, **kwargs: (
        f"Завантажено фото для книги (ID: {book_id})"
    ),
)
async def upload_book_image(
    book_id: int,
    file: UploadFile = File(...),
    session: SessionDep = None,
    user: LibrarianUserDep = None,
):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    librarian = get_librarian_from_user_dict(session, user)
    if librarian and book:
        check_book_library_access(session, book, librarian)

    contents = await file.read()

    file_ext = Path(file.filename).suffix.lower() if file.filename else ""

    if not file_ext and file.content_type:
        mime_to_ext = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }
        file_ext = mime_to_ext.get(file.content_type, "")

    if not file_ext:
        if contents.startswith(b"\xff\xd8\xff"):
            file_ext = ".jpg"
        elif contents.startswith(b"\x89PNG\r\n\x1a\n"):
            file_ext = ".png"
        elif contents.startswith(b"RIFF") and b"WEBP" in contents[:12]:
            file_ext = ".webp"

    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024} MB",
        )

    if book.image_url:
        old_image_path = UPLOAD_DIR / Path(book.image_url).name
        if old_image_path.exists():
            old_image_path.unlink()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{book_id}_{timestamp}{file_ext}"
    file_path = UPLOAD_DIR / filename

    with open(file_path, "wb") as f:
        f.write(contents)

    book.image_url = f"/static/books/{filename}"
    session.add(book)
    session.commit()
    session.refresh(book)

    return {"message": "Image uploaded successfully", "image_url": book.image_url}


@books_router.post("/{book_id}/notify")
async def subscribe_notification_route(
    book_id: int, session: SessionDep, user: UserDep
):
    return subscribe(session, book_id, user["user_id"])


@books_router.delete("/{book_id}/notify")
async def unsubscribe_notification_route(
    book_id: int, session: SessionDep, user: UserDep
):
    return unsubscribe(session, book_id, user["user_id"])


@books_router.get("/{book_id}/notify")
async def get_subscription_status_route(
    book_id: int, session: SessionDep, user: UserDep
):
    return get_subscription_status(session, book_id, user["user_id"])
