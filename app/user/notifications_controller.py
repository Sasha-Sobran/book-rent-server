from sqlalchemy.orm import Session
from sqlmodel import select

from app.models.user_notification import UserNotification


def get_user_notifications(session: Session, user_id: int, limit: int = 50):
    notifications = session.exec(
        select(UserNotification)
        .where(UserNotification.user_id == user_id)
        .order_by(UserNotification.created_at.desc())
        .limit(limit)
    ).all()
    return list(notifications)


def mark_as_read(session: Session, notification_id: int, user_id: int) -> bool:
    notification = session.exec(
        select(UserNotification).where(
            UserNotification.id == notification_id, UserNotification.user_id == user_id
        )
    ).first()

    if not notification:
        return False

    notification.is_read = True
    session.add(notification)
    session.commit()
    return True


def mark_all_as_read(session: Session, user_id: int):
    notifications = session.exec(
        select(UserNotification).where(
            UserNotification.user_id == user_id, UserNotification.is_read == False
        )
    ).all()

    for notification in notifications:
        notification.is_read = True
        session.add(notification)

    session.commit()


def get_unread_count(session: Session, user_id: int) -> int:
    from sqlalchemy import func

    result = session.exec(
        select(func.count(UserNotification.id)).where(
            UserNotification.user_id == user_id, UserNotification.is_read == False
        )
    ).first()
    return result or 0
