"""
Декоратори для автоматичного логування подій у журнал аудиту
"""

from functools import wraps
from typing import Callable, Optional, Any
from fastapi import Request
from sqlmodel import Session

from app.event_log.utils import log_audit_event


def _extract_session_and_user(
    *args, **kwargs
) -> tuple[Optional[Session], Optional[int], Optional[Request]]:
    """Допоміжна функція для витягування session, user_id та request з аргументів"""
    session: Optional[Session] = None
    user_id: Optional[int] = None
    request: Optional[Request] = None

    # Шукаємо session
    for arg in args:
        if isinstance(arg, Session):
            session = arg
            break
    if "session" in kwargs:
        session = kwargs["session"]

    # Шукаємо request
    for arg in args:
        if isinstance(arg, Request):
            request = arg
            break
    if "request" in kwargs:
        request = kwargs["request"]

    # Шукаємо user_id з user dependency
    if "user" in kwargs:
        user = kwargs["user"]
        if isinstance(user, dict) and "user_id" in user:
            user_id = user["user_id"]

    return session, user_id, request


def audit_log(
    action_type: str,
    entity_type: str,
    get_entity_id: Optional[Callable] = None,
    get_description: Optional[Callable] = None,
    get_old_values: Optional[Callable] = None,
    get_new_values: Optional[Callable] = None,
    get_additional_metadata: Optional[Callable] = None,
):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Отримуємо session, user_id, request перед виконанням (для old_values)
            session, user_id, request = _extract_session_and_user(*args, **kwargs)

            # Отримуємо old_values ДО виконання функції (для update/delete)
            old_values = None
            if get_old_values:
                try:
                    old_values = get_old_values(None, *args, **kwargs)
                except Exception:
                    pass

            # Виконуємо оригінальну функцію
            result = await func(*args, **kwargs)

            # Якщо немає session, не логуємо
            if not session:
                return result

            # Отримуємо дані для логування
            entity_id = None
            if get_entity_id:
                try:
                    entity_id = get_entity_id(result, *args, **kwargs)
                except Exception:
                    pass

            description = f"{action_type.capitalize()} {entity_type}"
            if get_description:
                try:
                    custom_desc = get_description(result, *args, **kwargs)
                    if custom_desc:
                        description = custom_desc
                except Exception:
                    pass

            new_values = None
            if get_new_values:
                try:
                    new_values = get_new_values(result, *args, **kwargs)
                except Exception:
                    pass

            additional_metadata = None
            if get_additional_metadata:
                try:
                    additional_metadata = get_additional_metadata(
                        result, *args, **kwargs
                    )
                except Exception:
                    pass

            # Логуємо подію
            try:
                log_audit_event(
                    session=session,
                    action_type=action_type,
                    entity_type=entity_type,
                    description=description,
                    user_id=user_id,
                    entity_id=entity_id,
                    old_values=old_values,
                    new_values=new_values,
                    additional_metadata=additional_metadata,
                    request=request,
                )
            except Exception as e:
                print(f"Помилка логування події: {e}")

            return result

        return wrapper

    return decorator


def audit_log_sync(
    action_type: str,
    entity_type: str,
    get_entity_id: Optional[Callable] = None,
    get_description: Optional[Callable] = None,
    get_old_values: Optional[Callable] = None,
    get_new_values: Optional[Callable] = None,
    get_additional_metadata: Optional[Callable] = None,
):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Отримуємо session перед виконанням (для old_values)
            session, user_id, _ = _extract_session_and_user(*args, **kwargs)

            # Отримуємо old_values ДО виконання функції (для update/delete)
            old_values = None
            if get_old_values:
                try:
                    old_values = get_old_values(None, *args, **kwargs)
                except Exception:
                    pass

            # Виконуємо оригінальну функцію
            result = func(*args, **kwargs)

            if not session:
                return result

            # Отримуємо дані для логування
            entity_id = None
            if get_entity_id:
                try:
                    entity_id = get_entity_id(result, *args, **kwargs)
                except Exception:
                    pass

            description = f"{action_type.capitalize()} {entity_type}"
            if get_description:
                try:
                    custom_desc = get_description(result, *args, **kwargs)
                    if custom_desc:
                        description = custom_desc
                except Exception:
                    pass

            new_values = None
            if get_new_values:
                try:
                    new_values = get_new_values(result, *args, **kwargs)
                except Exception:
                    pass

            additional_metadata = None
            if get_additional_metadata:
                try:
                    additional_metadata = get_additional_metadata(
                        result, *args, **kwargs
                    )
                except Exception:
                    pass

            # Логуємо подію (без request, бо це синхронна функція)
            try:
                log_audit_event(
                    session=session,
                    action_type=action_type,
                    entity_type=entity_type,
                    description=description,
                    user_id=user_id,
                    entity_id=entity_id,
                    old_values=old_values,
                    new_values=new_values,
                    additional_metadata=additional_metadata,
                    request=None,
                )
            except Exception as e:
                print(f"Помилка логування події: {e}")

            return result

        return wrapper

    return decorator
