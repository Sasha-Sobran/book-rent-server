from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.librarian import Librarian


def get_librarian_by_user_id(session: Session, user_id: int) -> Librarian | None:
    result = session.exec(select(Librarian).where(Librarian.user_id == user_id))
    return result.first()


def require_librarian_by_user_id(session: Session, user_id: int) -> Librarian:
    librarian = get_librarian_by_user_id(session, user_id)
    if not librarian:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Current user is not linked to a librarian profile",
        )
    return librarian


def get_librarian_from_user_dict(session: Session, user: dict) -> Librarian | None:
    if user.get("role_name") != "librarian":
        return None
    return get_librarian_by_user_id(session, user["user_id"])
