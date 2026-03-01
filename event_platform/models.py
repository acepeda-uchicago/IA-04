from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class RegistrationStatus(Enum):
    CONFIRMED = "confirmed"
    WAITLISTED = "waitlisted"
    CANCELLED = "cancelled"


class EventStatus(Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"


@dataclass
class User:
    """Represents a platform user. Authentication is out of scope."""
    id: str
    name: str
    email: str

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r})"


@dataclass
class Event:
    """
    Core event entity. Holds all event data and current status.
    id is assigned by the service layer, not the caller.
    """
    id: int
    title: str
    description: str
    date: datetime
    duration: float
    venue: str
    capacity: int
    status: EventStatus = EventStatus.ACTIVE
    organizer_id: Optional[str] = None

    def __repr__(self) -> str:
        return (
            f"Event(id={self.id}, title={self.title!r}, date={self.date.isoformat()}, "
            f"venue={self.venue!r}, capacity={self.capacity}, status={self.status.value})"
        )


@dataclass
class Registration:
    """
    Represents a user's registration for an event.
    Status is CONFIRMED or WAITLISTED depending on capacity at time of registration.
    """
    id: int
    event_id: int
    user_id: str
    status: RegistrationStatus
    registered_at: datetime = field(default_factory=datetime.now)

    def __repr__(self) -> str:
        return (
            f"Registration(id={self.id}, event_id={self.event_id}, "
            f"user_id={self.user_id!r}, status={self.status.value})"
        )