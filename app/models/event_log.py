from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel


class EventLog(SQLModel, table=True):
    __tablename__ = "event_log"

    id: int = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    action_type: str
    entity_type: str
    entity_id: Optional[int] = Field(default=None)
    description: str
    event_metadata: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    ip_address: Optional[str] = Field(default=None)
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True))
    )

    user: Optional["User"] = Relationship(back_populates="event_logs")

    class Config:
        arbitrary_types_allowed = True
