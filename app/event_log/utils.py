"""
Утиліти для автоматичного логування подій у журнал аудиту.

ВАЖЛИВО: Журнал аудиту призначений для збереження незмінної історії всіх важливих дій.
Записи не можуть бути змінені або видалені після створення.
"""

from typing import Optional
from sqlmodel import Session
from fastapi import Request

from app.event_log.controllers import create_event_log


def log_audit_event(
    session: Session,
    action_type: str,
    entity_type: str,
    description: str,
    user_id: Optional[int] = None,
    entity_id: Optional[int] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    additional_metadata: Optional[dict] = None,
    request: Optional[Request] = None,
) -> None:
    # Формуємо metadata з усіх даних
    metadata = {}

    if old_values:
        metadata["old_values"] = old_values

    if new_values:
        metadata["new_values"] = new_values

    if additional_metadata:
        metadata.update(additional_metadata)

    # Отримуємо IP адресу
    ip_address = None
    if request:
        # Отримуємо IP адресу з заголовків (для випадку, коли є проксі)
        ip_address = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.headers.get("X-Real-IP", "")
            or (request.client.host if request.client else None)
        )

    create_event_log(
        session=session,
        action_type=action_type,
        entity_type=entity_type,
        description=description,
        user_id=user_id,
        entity_id=entity_id,
        event_metadata=metadata if metadata else None,
        ip_address=ip_address,
    )
