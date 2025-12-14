from sqlalchemy.orm import Session
from sqlmodel import select

from app.models.book_notification import BookNotification


def subscribe(session: Session, book_id: int, user_id: int) -> dict:
    existing = session.exec(
        select(BookNotification).where(
            BookNotification.book_id == book_id, BookNotification.user_id == user_id
        )
    ).first()

    if existing:
        return {"message": "Already subscribed", "subscribed": True}

    notification = BookNotification(book_id=book_id, user_id=user_id)
    session.add(notification)
    session.commit()
    return {"message": "Subscribed", "subscribed": True}


def unsubscribe(session: Session, book_id: int, user_id: int) -> dict:
    notification = session.exec(
        select(BookNotification).where(
            BookNotification.book_id == book_id, BookNotification.user_id == user_id
        )
    ).first()

    if not notification:
        return {"message": "Not subscribed", "subscribed": False}

    session.delete(notification)
    session.commit()
    return {"message": "Unsubscribed", "subscribed": False}


def get_subscription_status(session: Session, book_id: int, user_id: int) -> dict:
    notification = session.exec(
        select(BookNotification).where(
            BookNotification.book_id == book_id, BookNotification.user_id == user_id
        )
    ).first()

    return {"subscribed": notification is not None}
