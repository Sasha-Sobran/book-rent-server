from sqlmodel import Session, select

from app.models.category import Category
from app.models.genre import Genre
from app.models.penalty_type import PenaltyType
from app.models.reader_category import ReaderCategory


def get_genres(session: Session) -> list[Genre]:
    return list(session.exec(select(Genre)).all())


def get_categories(session: Session) -> list[Category]:
    return list(session.exec(select(Category)).all())


def get_reader_categories(session: Session) -> list[ReaderCategory]:
    return list(session.exec(select(ReaderCategory)).all())


def get_penalty_types(session: Session) -> list[PenaltyType]:
    return list(session.exec(select(PenaltyType)).all())


def create_genre(session: Session, name: str) -> Genre:
    genre = Genre(name=name)
    session.add(genre)
    session.commit()
    session.refresh(genre)
    return genre


def delete_genre(session: Session, genre_id: int) -> bool:
    from sqlmodel import delete
    from app.models.book import BookGenre

    genre = session.get(Genre, genre_id)
    if not genre:
        return False

    session.exec(delete(BookGenre).where(BookGenre.genre_id == genre_id))

    session.delete(genre)
    session.commit()
    return True


def create_category(session: Session, name: str) -> Category:
    category = Category(name=name)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def delete_category(session: Session, category_id: int) -> bool:
    from sqlmodel import delete
    from app.models.book import BookCategory

    category = session.get(Category, category_id)
    if not category:
        return False

    session.exec(delete(BookCategory).where(BookCategory.category_id == category_id))

    session.delete(category)
    session.commit()
    return True


def create_reader_category(
    session: Session, name: str, discount_percentage: int
) -> ReaderCategory:
    category = ReaderCategory(name=name, discount_percentage=discount_percentage)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def update_reader_category(
    session: Session, category_id: int, name: str, discount_percentage: int
) -> ReaderCategory | None:
    category = session.get(ReaderCategory, category_id)
    if not category:
        return None
    category.name = name
    category.discount_percentage = discount_percentage
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def delete_reader_category(session: Session, category_id: int) -> bool:
    from sqlmodel import select
    from fastapi import HTTPException

    category = session.get(ReaderCategory, category_id)
    if not category:
        return False

    readers_with_category = session.exec(
        select(Reader).where(Reader.reader_category_id == category_id)
    ).first()
    if readers_with_category:
        raise HTTPException(
            status_code=400, detail="Cannot delete category with assigned readers"
        )

    session.delete(category)
    session.commit()
    return True


def create_penalty_type(session: Session, name: str) -> PenaltyType:
    penalty_type = PenaltyType(name=name)
    session.add(penalty_type)
    session.commit()
    session.refresh(penalty_type)
    return penalty_type


def delete_penalty_type(session: Session, type_id: int) -> bool:
    from sqlmodel import select
    from app.models.penalty import Penalty
    from fastapi import HTTPException

    penalty_type = session.get(PenaltyType, type_id)
    if not penalty_type:
        return False

    penalties_with_type = session.exec(
        select(Penalty).where(Penalty.penalty_type_id == type_id)
    ).first()
    if penalties_with_type:
        raise HTTPException(
            status_code=400, detail="Cannot delete penalty type with assigned penalties"
        )

    session.delete(penalty_type)
    session.commit()
    return True
