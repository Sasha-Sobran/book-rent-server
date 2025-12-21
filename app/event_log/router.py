from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query, Depends
from sqlmodel import Session

from app.common.dependencies import SessionDep, RootUserDep
from app.event_log.controllers import get_event_logs, get_event_log_by_id
from app.event_log.schemas import (
    EventLogResponse,
    EventLogFilters,
    EventLogListResponse,
)

event_log_router = APIRouter(prefix="/event-log", tags=["event-log"])


@event_log_router.get("/", response_model=EventLogListResponse)
async def list_event_logs_route(
    session: SessionDep,
    user: RootUserDep,
    user_id: Optional[int] = Query(default=None),
    action_type: Optional[str] = Query(default=None),
    entity_type: Optional[str] = Query(default=None),
    entity_id: Optional[int] = Query(default=None),
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    """Отримати список подій з фільтрацією"""
    exclude_root = False
    
    filters = EventLogFilters(
        user_id=user_id,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        date_from=date_from,
        date_to=date_to,
        search=search,
        limit=limit,
        offset=offset,
    )
    events, total = get_event_logs(session, filters, exclude_root_events=exclude_root)
    return EventLogListResponse(events=events, total=total)


@event_log_router.get("/{event_id}", response_model=EventLogResponse)
async def get_event_log_route(
    event_id: int,
    session: SessionDep,
    user: RootUserDep,  # Тільки адміни можуть переглядати журнал аудиту
):
    """Отримати одну подію за ID"""
    return get_event_log_by_id(session, event_id)
