from datetime import datetime
from typing import Optional

from .models import Event, Registration, RegistrationStatus, EventStatus

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

# Custom exceptions to be called by services
class EventNotFoundError(Exception):
    """Raised when an event that does not exist."""
    pass

class DuplicateRegistrationError(Exception):
    """Raised when a user attempts to register for an event they are already registered for."""
    pass


# Event Service
class EventService:
    def __init__(self):
        self._events: dict[int, Event] = {}
        self._registrations: dict[int, Registration] = {}
        self._event_id_counter: int = 0
        self._registration_id_counter: int = 0

    def create_event(
        self,
        title: str,
        description: str,
        date: str,
        duration:float,
        venue: str,
        capacity: int,
        organizer_id: Optional[str] = None) -> Event:
        """
        Creates and stores a new event.
            title: title of event
            decription: description of event
            date: date in 

        Returns newly created Event with an assigned id.

        Raises ValueError If any required field is missing/empty, the date is in the past,
            or capacity is not a positive integer.
        """
        #  validate string fields
        if not title or not title.strip():
            raise ValueError("title is required and cannot be empty.")
        if not description or not description.strip():
            raise ValueError("description is required and cannot be empty.")
        if not venue or not venue.strip():
            raise ValueError("venue is required and cannot be empty.")

        # validate date
        if not date or not str(date).strip():
            raise ValueError("date is required and cannot be empty.")

        parsed_date = self._parse_date(date)

        if parsed_date < datetime.now():
            raise ValueError(f"Event date {parsed_date.isoformat()} is in the past.")

        # capacity
        if not isinstance(capacity, int) or isinstance(capacity, bool):
            raise ValueError("capacity must be an integer.")
        if capacity <= 0:
            raise ValueError("capacity must be a positive integer.")

        # store event
        self._event_id_counter += 1
        event = Event(
            id=self._event_id_counter,
            title=title.strip(),
            description=description.strip(),
            date=parsed_date,
            venue=venue.strip(),
            duration=duration,
            capacity=capacity,
            organizer_id=organizer_id,
        )
        self._events[event.id] = event
        return event

    def get_event(self, event_id: int) -> Event:
        """
        Retrieves a single event by id. Raises EventNotFoundError 
        if no event with the given id exists.
        """
        event = self._events.get(event_id)
        if event is None:
            raise EventNotFoundError(f"No event found with id={event_id}.")
        return event

    def list_events(self) -> list[Event]:
        """Returns all active events, sorted by date ascending."""
        return sorted(
            [e for e in self._events.values() if e.status == EventStatus.ACTIVE],
            key=lambda e: e.date,
        )

    def cancel_event(self, event_id: int) -> Event:
        """
        Marks an event as cancelled. Raises EventNotFoundError
        if no event with the given id exists.
        """
        event = self.get_event(event_id)
        event.status = EventStatus.CANCELLED
        return event

    # Registration
    def register(self, event_id: int, user_id: str) -> Registration:
        """
        Registers a user for an event. Returns registration. Raises 
        EventNotFoundError if the event does not exist, DuplicateRegistrationError 
        if the user is already registered, ValueError if no user id

        Business rules
        --------------
        - The event must exist.
        - The user must not already have an active (CONFIRMED or WAITLISTED)
          registration for this event.
        - If confirmed registrations < capacity: status = CONFIRMED.
        - If confirmed registrations >= capacity: status = WAITLISTED.
        """
        if not user_id or not str(user_id).strip():
            raise ValueError("user_id is required and cannot be empty.")

        event = self.get_event(event_id)

        # Check for duplicate active registration
        for reg in self._registrations.values():
            if (
                reg.event_id == event_id
                and reg.user_id == user_id
                and reg.status != RegistrationStatus.CANCELLED
            ):
                raise DuplicateRegistrationError(
                    f"User {user_id!r} is already registered for event {event_id}."
                )

        # Determine confirmed vs waitlisted
        confirmed = self._confirmed_count(event_id)
        status = (
            RegistrationStatus.CONFIRMED
            if confirmed < event.capacity
            else RegistrationStatus.WAITLISTED
        )

        self._registration_id_counter += 1
        registration = Registration(
            id=self._registration_id_counter,
            event_id=event_id,
            user_id=user_id,
            status=status,
        )
        self._registrations[registration.id] = registration
        return registration

    def cancel_registration(self, event_id: int, user_id: str) -> Registration:
        """
        Cancels a user's registration for an event an promotes waitlisted registration to confirmed registration.

        Raises EventNotFoundError if the event does not exist.
        and ValueError if no active registration exists for this user/event
        """
        self.get_event(event_id)  # ensure event exists

        # Find the active registration for this user
        target = None
        for reg in self._registrations.values():
            if (
                reg.event_id == event_id
                and reg.user_id == user_id
                and reg.status != RegistrationStatus.CANCELLED
            ):
                target = reg
                break

        if target is None:
            raise ValueError(
                f"No active registration found for user {user_id!r} on event {event_id}."
            )

        was_confirmed = target.status == RegistrationStatus.CONFIRMED
        target.status = RegistrationStatus.CANCELLED

        # Promote first waitlisted user if a confirmed slot just opened
        if was_confirmed:
            waitlist = self._get_waitlist(event_id)
            if waitlist:
                waitlist[0].status = RegistrationStatus.CONFIRMED

        return target

    def get_registrations_for_event(self, event_id: int) -> list[Registration]:
        # Returns all registrations for a given event, ordered by registration time.
        # Raises EventNotFoundError If the event does not exist.
        self.get_event(event_id)  # ensure event exists
        return sorted(
            [r for r in self._registrations.values() if r.event_id == event_id],
            key=lambda r: r.registered_at,
        )

    # I though I was going to have to use this but I do not currently.
    def get_registrations_for_user(self, user_id: str) -> list[Registration]:
        # Returns registrations for a given user sorted by event date
        active = [
            r for r in self._registrations.values()
            if r.user_id == user_id and r.status != RegistrationStatus.CANCELLED
        ]
        # Sort by the date of the associated event
        return sorted(active, key=lambda r: self._events[r.event_id].date)


    # Event Search (Elective)
    def search_events(
        self,
        keyword: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        venue: Optional[str] = None,
    ) -> list[Event]:
        """
        Returns active events matching all provided filters.  Matching events sorted by date ascending.

        Raises ValueError if both date_from and date_to are provided but date_from > date_to,
            or if any date string cannot be parsed.
        """
        parsed_from = self._parse_date(date_from) if date_from else None
        parsed_to = self._parse_date(date_to) if date_to else None

        if parsed_from and parsed_to and parsed_from > parsed_to:
            raise ValueError(
                f"date_from ({date_from}) must not be later than date_to ({date_to})."
            )

        results = []
        for event in self._events.values():
            # verify event active
            if event.status != EventStatus.ACTIVE:
                continue
            # if keyword entered, check if substring in title or description
            if keyword and keyword.lower() not in event.title.lower() \
                    and keyword.lower() not in event.description.lower():
                continue
            # if date from entered, check valid date
            if parsed_from and event.date < parsed_from:
                continue
            # if date to entered, check valid date
            if parsed_to and event.date > parsed_to:
                continue
            # if venue entered, check if substring in venue
            if venue and venue.lower() not in event.venue.lower():
                continue
            results.append(event)

        return sorted(results, key=lambda e: e.date)

    # Private helpers
    def _confirmed_count(self, event_id: int) -> int:
        # Returns the number of confirmed event registrations
        registration = [
                        1 for r in self._registrations.values()
                        if r.event_id == event_id and r.status == RegistrationStatus.CONFIRMED
                        ]
            
        return sum(registration)

    def _get_waitlist(self, event_id: int) -> list[Registration]:
        # Returns waitlisted event registrations, ordered by registration time.
        unsorted = [
                    r for r in self._registrations.values()
                    if r.event_id == event_id and r.status == RegistrationStatus.WAITLISTED
                    ]
        return sorted(unsorted,key=lambda r: r.registered_at)

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """
        Parses datetime string into a datetime object.
        Accepts "YYYY-MM-DDTHH:MM:SS".

        Raises ValueError if the string cannot be parsed.
        """
        try:
            return datetime.strptime(date_str, DATE_FORMAT)
        except ValueError:
            raise ValueError(
                f"Cannot parse date {date_str!r}. "
                "Expected format: 'YYYY-MM-DDTHH:MM:SS'."
            )