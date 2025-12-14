from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class EventLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    action_type: str
    entity_type: str
    entity_id: Optional[int] = None
    description: str
    metadata: Optional[dict] = None
    ip_address: Optional[str] = None
    timestamp: datetime


class EventLogFilters(BaseModel):
    user_id: Optional[int] = None
    action_type: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None
    limit: int = 100
    offset: int = 0


class EventLogListResponse(BaseModel):
    events: list[EventLogResponse]
    total: int
