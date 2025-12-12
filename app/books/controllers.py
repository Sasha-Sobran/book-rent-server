from fastapi import HTTPException, status
from sqlmodel import Session, select, delete

from app.models.book import Book, BookCategory, BookGenre
from app.models.category import Category
from app.models.genre import Genre
from app.models.library import Library
from app.models.librarian import Librarian
from app.books.schemas import BookCreate, BookResponse, BookUpdate


def list_books(
    session: Session,
    library_id: int | None = None,
    search: str | None = None,
    category_ids: list[int] | None = None,
    genre_ids: list[int] | None = None,
) -> list[BookResponse]:
    query = select(Book).distinct()
    if library_id is not None:
        query = query.where(Book.library_id == library_id)
    if search:
        like = f"%{search}%"
        query = query.where((Book.title.ilike(like)) | (Book.author.ilike(like)))
    if category_ids:
        query = query.join(BookCategory).where(BookCategory.category_id.in_(category_ids))
    if genre_ids:
        query = query.join(BookGenre).where(BookGenre.genre_id.in_(genre_ids))
    books = session.exec(query).all()
    for book in books:
        session.refresh(book, attribute_names=["library", "categories", "genres"])
    return [_to_response(b) for b in books]


def get_book(session: Session, book_id: int) -> BookResponse | None:
    book = session.get(Book, book_id)
    if not book:
        return None
    return _to_response(book)


def create_book(session: Session, data: BookCreate, librarian_user_id: int | None = None) -> BookResponse:
    library_id = data.library_id
    if librarian_user_id is not None:
        librarian = session.exec(select(Librarian).where(Librarian.user_id == librarian_user_id)).scalar_one_or_none()
        if not librarian:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Current user is not a librarian")
        library_id = librarian.library_id
    _validate_library(session, library_id)
    book = Book(
        title=data.title,
        author=data.author,
        price=data.price,
        publish_year=data.publish_year,
        quantity=data.quantity,
        library_id=library_id,
    )
    session.add(book)
    session.commit()
    session.refresh(book)
    _apply_relations(
        session,
        book,
        category_ids=data.category_ids,
        genre_ids=data.genre_ids,
        new_categories=data.new_categories,
        new_genres=data.new_genres,
    )
    session.commit()
    session.refresh(book)
    return _to_response(book)


def update_book(session: Session, book_id: int, data: BookUpdate) -> BookResponse | None:
    book = session.get(Book, book_id)
    if not book:
        return None
    if data.library_id is not None:
        _validate_library(session, data.library_id)
        book.library_id = data.library_id
    if data.title is not None:
        book.title = data.title
    if data.author is not None:
        book.author = data.author
    if data.price is not None:
        book.price = data.price
    if data.publish_year is not None:
        book.publish_year = data.publish_year
    if data.quantity is not None:
        book.quantity = data.quantity
    if any(
        v is not None
        for v in (data.category_ids, data.genre_ids, data.new_categories, data.new_genres)
    ):
        _apply_relations(
            session,
            book,
            category_ids=data.category_ids,
            genre_ids=data.genre_ids,
            new_categories=data.new_categories,
            new_genres=data.new_genres,
        )
    session.add(book)
    session.commit()
    session.refresh(book)
    return _to_response(book)


def delete_book(session: Session, book_id: int) -> bool:
    book = session.get(Book, book_id)
    if not book:
        return False
    session.delete(book)
    session.commit()
    return True


def _validate_library(session: Session, library_id: int):
    library = session.get(Library, library_id)
    if library is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Library not found",
        )


def _to_response(book: Book) -> BookResponse:
    categories = [c.name for c in book.categories] if book.categories else []
    genres = [g.name for g in book.genres] if book.genres else []
    return BookResponse(
        id=book.id,
        title=book.title,
        author=book.author,
        price=book.price,
        publish_year=book.publish_year,
        quantity=book.quantity,
        library_id=book.library_id,
        library_name=book.library.name if book.library else None,
        categories=categories,
        genres=genres,
    )


def _apply_relations(
    session: Session,
    book: Book,
    category_ids: list[int] | None = None,
    genre_ids: list[int] | None = None,
    new_categories: list[str] | None = None,
    new_genres: list[str] | None = None,
):
    category_ids = category_ids or []
    genre_ids = genre_ids or []
    new_categories = [c.strip() for c in (new_categories or []) if c and c.strip()]
    new_genres = [g.strip() for g in (new_genres or []) if g and g.strip()]

    for name in new_categories:
        existing = session.exec(select(Category).where(Category.name == name)).first()
        if existing is None:
            cat = Category(name=name)
            session.add(cat)
            session.commit()
            session.refresh(cat)
            category_ids.append(cat.id)
        else:
            category_ids.append(existing.id)

    for name in new_genres:
        existing = session.exec(select(Genre).where(Genre.name == name)).first()
        if existing is None:
            gen = Genre(name=name)
            session.add(gen)
            session.commit()
            session.refresh(gen)
            genre_ids.append(gen.id)
        else:
            genre_ids.append(existing.id)

    session.exec(delete(BookCategory).where(BookCategory.book_id == book.id))
    session.exec(delete(BookGenre).where(BookGenre.book_id == book.id))
    session.commit()

    book.categories = []
    book.genres = []

    if category_ids:
        cats = session.exec(select(Category).where(Category.id.in_(category_ids))).all()
        book.categories = list(cats)
    if genre_ids:
        gens = session.exec(select(Genre).where(Genre.id.in_(genre_ids))).all()
        book.genres = list(gens)
    session.add(book)

