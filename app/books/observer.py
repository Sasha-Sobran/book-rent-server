from sqlalchemy.orm import Session
from sqlmodel import select
import asyncio

from app.models.book import Book
from app.models.book_notification import BookNotification
from app.models.user_notification import UserNotification
from app.websocket.manager import WebSocketManager


class BookAvailabilityObserver:
    @staticmethod
    def notify_subscribers(session: Session, book_id: int):
        book = session.get(Book, book_id)
        if not book or book.quantity <= 0:
            return

        notifications = session.exec(
            select(BookNotification).where(BookNotification.book_id == book_id)
        ).all()

        if not notifications:
            return

        user_notifications = []
        for notification in notifications:
            user_notification = UserNotification(
                user_id=notification.user_id,
                title="Книга в наявності",
                message=f'Книга "{book.title}" тепер доступна для оренди',
                book_id=book_id,
            )
            session.add(user_notification)
            session.delete(notification)
            user_notifications.append((user_notification, notification.user_id))

        session.commit()

        for user_notification, user_id in user_notifications:
            session.refresh(user_notification)
            notification_data = {
                "type": "notification",
                "notification": {
                    "id": user_notification.id,
                    "title": user_notification.title,
                    "message": user_notification.message,
                    "is_read": user_notification.is_read,
                    "created_at": user_notification.created_at.isoformat(),
                    "book_id": user_notification.book_id,
                },
            }
            try:
                manager = WebSocketManager.get_instance()
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(
                        manager.send_personal_message(notification_data, user_id)
                    )
                else:
                    loop.run_until_complete(
                        manager.send_personal_message(notification_data, user_id)
                    )
            except Exception:
                pass
