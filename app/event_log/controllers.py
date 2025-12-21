from datetime import datetime
from typing import Optional
from sqlmodel import Session, select, or_, and_, func
from fastapi import HTTPException, status

from app.models.event_log import EventLog
from app.models.user import User
from app.event_log.schemas import EventLogResponse, EventLogFilters
from app.common.db_utils import save_and_refresh


def create_event_log(
    session: Session,
    action_type: str,
    entity_type: str,
    description: str,
    user_id: Optional[int] = None,
    entity_id: Optional[int] = None,
    event_metadata: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> EventLog:
    """
    Створює запис у журналі аудиту.

    ВАЖЛИВО: Записи в журналі аудиту не можуть бути змінені або видалені.
    Це забезпечує цілісність та незмінність історії дій.
    """
    event = EventLog(
        user_id=user_id,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        event_metadata=event_metadata,
        ip_address=ip_address,
    )
    return save_and_refresh(session, event)


def get_event_logs(
    session: Session,
    filters: EventLogFilters,
    exclude_root_events: bool = False,
) -> tuple[list[EventLogResponse], int]:
    """Отримує список подій з фільтрацією та пагінацією"""
    from app.models.role import Role
    
    query = select(EventLog, User).outerjoin(User, EventLog.user_id == User.id)

    conditions = []
    
    if exclude_root_events:
        root_role = session.exec(select(Role).where(Role.name.ilike("root"))).first()
        if root_role:
            conditions.append(User.role_id != root_role.id)

    if filters.user_id:
        conditions.append(EventLog.user_id == filters.user_id)

    if filters.action_type:
        conditions.append(EventLog.action_type == filters.action_type)

    if filters.entity_type:
        conditions.append(EventLog.entity_type == filters.entity_type)

    if filters.entity_id:
        conditions.append(EventLog.entity_id == filters.entity_id)

    if filters.date_from:
        conditions.append(EventLog.timestamp >= filters.date_from)

    if filters.date_to:
        conditions.append(EventLog.timestamp <= filters.date_to)

    if filters.search:
        conditions.append(EventLog.description.ilike(f"%{filters.search}%"))

    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(EventLog).outerjoin(User, EventLog.user_id == User.id)
    count_conditions = []
    if exclude_root_events:
        root_role = session.exec(select(Role).where(Role.name.ilike("root"))).first()
        if root_role:
            count_conditions.append(User.role_id != root_role.id)
    if filters.user_id:
        count_conditions.append(EventLog.user_id == filters.user_id)
    if filters.action_type:
        count_conditions.append(EventLog.action_type == filters.action_type)
    if filters.entity_type:
        count_conditions.append(EventLog.entity_type == filters.entity_type)
    if filters.entity_id:
        count_conditions.append(EventLog.entity_id == filters.entity_id)
    if filters.date_from:
        count_conditions.append(EventLog.timestamp >= filters.date_from)
    if filters.date_to:
        count_conditions.append(EventLog.timestamp <= filters.date_to)
    if filters.search:
        count_conditions.append(EventLog.description.ilike(f"%{filters.search}%"))
    if count_conditions:
        count_query = count_query.where(and_(*count_conditions))
    total_count = session.exec(count_query).one()

    query = query.order_by(EventLog.timestamp.desc())
    query = query.offset(filters.offset).limit(filters.limit)

    results = session.exec(query).all()

    events = []
    for event, user in results:
        events.append(
            EventLogResponse(
                id=event.id,
                user_id=event.user_id,
                user_name=f"{user.surname} {user.name}" if user else None,
                action_type=event.action_type,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                description=event.description,
                metadata=event.event_metadata,
                ip_address=event.ip_address,
                timestamp=event.timestamp,
            )
        )

    return events, total_count


def get_event_log_by_id(session: Session, event_id: int) -> EventLogResponse:
    """Отримує одну подію за ID"""
    query = (
        select(EventLog, User)
        .outerjoin(User, EventLog.user_id == User.id)
        .where(EventLog.id == event_id)
    )
    result = session.exec(query).first()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event log not found"
        )

    event, user = result
    return EventLogResponse(
        id=event.id,
        user_id=event.user_id,
        user_name=f"{user.surname} {user.name}" if user else None,
        action_type=event.action_type,
        entity_type=event.entity_type,
        entity_id=event.entity_id,
        description=event.description,
        metadata=event.event_metadata,
        ip_address=event.ip_address,
        timestamp=event.timestamp,
    )
