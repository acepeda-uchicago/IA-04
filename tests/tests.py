
import pytest
from datetime import datetime, timedelta

from event_platform.services import EventService, EventNotFoundError, DuplicateRegistrationError
from event_platform.models import RegistrationStatus, EventStatus

# test helpers
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
FUTURE_DATE = (datetime.now() + timedelta(days=30)).strftime(DATE_FORMAT)
FUTURE_DATE_2 = (datetime.now() + timedelta(days=60)).strftime(DATE_FORMAT)
FUTURE_DATE_3 = (datetime.now() + timedelta(days=90)).strftime(DATE_FORMAT)
PAST_DATE = (datetime.now() - timedelta(days=1)).strftime(DATE_FORMAT)

def make_service():
    # Returns a fresh EventService
    return EventService()

def make_event(service, title="Tech Talk", capacity=10, venue="Room 101", date=None):
    # Create event for testing
    return service.create_event(
        title=title,
        description="A test event.",
        date=date or FUTURE_DATE,
        duration=1.0,
        venue=venue,
        capacity=capacity)

# begin tests
# create_event — happy path
class TestCreateEvent:
    def test_create_event_returns_event_with_assigned_id(self):
        service = make_service()
        event = make_event(service)
        assert event.id == 1
        assert event.title == "Tech Talk"

    def test_create_event_ids_increment(self):
        service = make_service()
        e1 = make_event(service, title="Event One")
        e2 = make_event(service, title="Event Two")
        assert e2.id == e1.id + 1

    def test_create_event_stores_all_fields(self):
        service = make_service()
        event = service.create_event(
            title="Spring Fest",
            description="Annual spring event.",
            date=FUTURE_DATE,
            duration=1.0,
            venue="Main Hall",
            capacity=200,
            organizer_id="user_1",
        )
        assert event.title == "Spring Fest"
        assert event.description == "Annual spring event."
        assert event.venue == "Main Hall"
        assert event.duration == 1.0
        assert event.capacity == 200
        assert event.organizer_id == "user_1"
        assert event.status == EventStatus.ACTIVE

    def test_create_event_accepts_datetime_string(self):
        service = make_service()
        future_dt = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%dT15:00:00")
        event = service.create_event(
            title="Workshop", description="Details.", date=future_dt, duration=1.0, venue="Lab", capacity=5
        )
        assert event.id is not None

    # validation (error raising)
    def test_create_event_raises_on_empty_title(self):
        service = make_service()
        with pytest.raises(ValueError, match="title"):
            service.create_event(title="", description="Desc.", date=FUTURE_DATE, duration=1.0, venue="Room", capacity=10)

    def test_create_event_raises_on_whitespace_title(self):
        service = make_service()
        with pytest.raises(ValueError, match="title"):
            service.create_event(title="   ", description="Desc.", date=FUTURE_DATE, duration=1.0, venue="Room", capacity=10)

    def test_create_event_raises_on_empty_venue(self):
        service = make_service()
        with pytest.raises(ValueError, match="venue"):
            service.create_event(title="Talk", description="Desc.", date=FUTURE_DATE, duration=1.0, venue="", capacity=10)

    def test_create_event_raises_on_empty_description(self):
        service = make_service()
        with pytest.raises(ValueError, match="description"):
            service.create_event(title="Talk", description="", date=FUTURE_DATE, duration=1.0, venue="Room", capacity=10)

    def test_create_event_raises_on_past_date(self):
        service = make_service()
        with pytest.raises(ValueError, match="past"):
            make_event(service, date=PAST_DATE)

    def test_create_event_raises_on_invalid_date_format(self):
        service = make_service()
        with pytest.raises(ValueError):
            make_event(service, date="not-a-date")

    # --- Validation: capacity ---

    def test_create_event_raises_on_zero_capacity(self):
        service = make_service()
        with pytest.raises(ValueError, match="capacity"):
            make_event(service, capacity=0)

    def test_create_event_raises_on_negative_capacity(self):
        service = make_service()
        with pytest.raises(ValueError, match="capacity"):
            make_event(service, capacity=-5)

    def test_create_event_raises_on_float_capacity(self):
        service = make_service()
        with pytest.raises(ValueError, match="capacity"):
            service.create_event(
                title="Talk", description="Desc.", date=FUTURE_DATE, duration=1.0, venue="Room", capacity=2.5
            )


# ---------------------------------------------------------------------------
# register — happy path
# ---------------------------------------------------------------------------

class TestRegister:

    def test_register_returns_confirmed_when_space_available(self):
        service = make_service()
        event = make_event(service, capacity=5)
        reg = service.register(event_id=event.id, user_id="user_1")
        assert reg.status == RegistrationStatus.CONFIRMED

    def test_register_multiple_users_all_confirmed_under_capacity(self):
        service = make_service()
        event = make_event(service, capacity=3)
        for i in range(1, 4):
            reg = service.register(event_id=event.id, user_id=f"user_{i}")
            assert reg.status == RegistrationStatus.CONFIRMED

    def test_register_returns_waitlisted_when_event_full(self):
        service = make_service()
        event = make_event(service, capacity=2)
        service.register(event_id=event.id, user_id="user_1")
        service.register(event_id=event.id, user_id="user_2")
        reg = service.register(event_id=event.id, user_id="user_3")
        assert reg.status == RegistrationStatus.WAITLISTED

    def test_register_exactly_at_capacity_is_confirmed(self):
        """The last seat should still be CONFIRMED, not waitlisted."""
        service = make_service()
        event = make_event(service, capacity=1)
        reg = service.register(event_id=event.id, user_id="user_1")
        assert reg.status == RegistrationStatus.CONFIRMED

    def test_register_one_over_capacity_is_waitlisted(self):
        service = make_service()
        event = make_event(service, capacity=1)
        service.register(event_id=event.id, user_id="user_1")
        reg = service.register(event_id=event.id, user_id="user_2")
        assert reg.status == RegistrationStatus.WAITLISTED

    # --- Error conditions ---

    def test_register_raises_on_nonexistent_event(self):
        service = make_service()
        with pytest.raises(EventNotFoundError):
            service.register(event_id=999, user_id="user_1")

    def test_register_raises_on_duplicate_confirmed(self):
        service = make_service()
        event = make_event(service, capacity=5)
        service.register(event_id=event.id, user_id="user_1")
        with pytest.raises(DuplicateRegistrationError):
            service.register(event_id=event.id, user_id="user_1")

    def test_register_raises_on_duplicate_waitlisted(self):
        """User already waitlisted should not be able to register again."""
        service = make_service()
        event = make_event(service, capacity=1)
        service.register(event_id=event.id, user_id="user_1")  # confirmed
        service.register(event_id=event.id, user_id="user_2")  # waitlisted
        with pytest.raises(DuplicateRegistrationError):
            service.register(event_id=event.id, user_id="user_2")

    def test_register_raises_on_empty_user_id(self):
        service = make_service()
        event = make_event(service, capacity=5)
        with pytest.raises(ValueError):
            service.register(event_id=event.id, user_id="")


# ---------------------------------------------------------------------------
# cancel_registration — waitlist promotion
# ---------------------------------------------------------------------------

class TestCancelRegistration:

    def test_cancel_confirmed_promotes_waitlisted_user(self):
        service = make_service()
        event = make_event(service, capacity=1)
        service.register(event_id=event.id, user_id="user_1")   # confirmed
        reg2 = service.register(event_id=event.id, user_id="user_2")  # waitlisted
        assert reg2.status == RegistrationStatus.WAITLISTED

        service.cancel_registration(event_id=event.id, user_id="user_1")

        # user_2 should now be confirmed
        updated = service.get_registrations_for_event(event.id)
        user2_reg = next(r for r in updated if r.user_id == "user_2")
        assert user2_reg.status == RegistrationStatus.CONFIRMED

    def test_cancel_waitlisted_does_not_promote(self):
        """Cancelling a waitlisted registration should not affect confirmed count."""
        service = make_service()
        event = make_event(service, capacity=1)
        service.register(event_id=event.id, user_id="user_1")   # confirmed
        service.register(event_id=event.id, user_id="user_2")   # waitlisted
        service.register(event_id=event.id, user_id="user_3")   # waitlisted

        service.cancel_registration(event_id=event.id, user_id="user_2")

        # user_1 still confirmed; user_3 still waitlisted
        regs = {r.user_id: r for r in service.get_registrations_for_event(event.id)}
        assert regs["user_1"].status == RegistrationStatus.CONFIRMED
        assert regs["user_3"].status == RegistrationStatus.WAITLISTED

    def test_cancel_registration_raises_on_no_active_registration(self):
        service = make_service()
        event = make_event(service, capacity=5)
        with pytest.raises(ValueError):
            service.cancel_registration(event_id=event.id, user_id="user_nobody")

    def test_cancel_registration_raises_on_nonexistent_event(self):
        service = make_service()
        with pytest.raises(EventNotFoundError):
            service.cancel_registration(event_id=999, user_id="user_1")

    def test_cancelled_user_can_reregister(self):
        """After cancelling, a user should be able to register again."""
        service = make_service()
        event = make_event(service, capacity=5)
        service.register(event_id=event.id, user_id="user_1")
        service.cancel_registration(event_id=event.id, user_id="user_1")
        reg = service.register(event_id=event.id, user_id="user_1")
        assert reg.status == RegistrationStatus.CONFIRMED


# ---------------------------------------------------------------------------
# search_events (elective)
# ---------------------------------------------------------------------------

class TestSearchEvents:
    def _setup_events(self, service):
        """Create a set of diverse events for search testing."""
        e1 = service.create_event(
            title="Python Workshop",
            description="Intro to Python programming.",
            date=FUTURE_DATE,
            duration=1.0,
            venue="Crerar Lab",
            capacity=30,
        )
        e2 = service.create_event(
            title="Spring Cultural Festival",
            description="Celebration of global cultures on campus.",
            date=FUTURE_DATE_2,
            duration=1.0,
            venue="Main Quad",
            capacity=200,
        )
        e3 = service.create_event(
            title="Career Fair",
            description="Meet recruiters from top tech companies.",
            date=FUTURE_DATE_3,
            duration=1.0,
            venue="Crerar Lab",
            capacity=100,
        )
        return e1, e2, e3

    def test_search_by_keyword_matches_title(self):
        service = make_service()
        self._setup_events(service)
        results = service.search_events(keyword="Python")
        assert len(results) == 1
        assert results[0].title == "Python Workshop"

    def test_search_by_keyword_matches_description(self):
        service = make_service()
        self._setup_events(service)
        results = service.search_events(keyword="recruiters")
        assert len(results) == 1
        assert results[0].title == "Career Fair"

    def test_search_by_keyword_is_case_insensitive(self):
        service = make_service()
        self._setup_events(service)
        results = service.search_events(keyword="python")
        assert len(results) == 1

    def test_search_by_venue(self):
        service = make_service()
        self._setup_events(service)
        results = service.search_events(venue="Crerar")
        assert len(results) == 2

    def test_search_by_date_range(self):
        service = make_service()
        self._setup_events(service)
        results = service.search_events(date_from=FUTURE_DATE, date_to=FUTURE_DATE_2)
        assert len(results) == 2

    # TODO
    def test_search_combined_filters(self):
        service = make_service()
        self._setup_events(service)
        results = service.search_events(keyword="Recruiters", venue="Crerar", date_from=FUTURE_DATE_3)
        assert len(results) == 1
        assert results[0].title == "Career Fair"

    def test_search_no_filters_returns_all_active(self):
        service = make_service()
        self._setup_events(service)
        results = service.search_events()
        assert len(results) == 3

    def test_search_excludes_cancelled_events(self):
        service = make_service()
        e1, e2, e3 = self._setup_events(service)
        service.cancel_event(e1.id)
        results = service.search_events()
        assert all(r.id != e1.id for r in results)

    def test_search_returns_results_sorted_by_date(self):
        service = make_service()
        self._setup_events(service)
        results = service.search_events()
        dates = [r.date for r in results]
        assert dates == sorted(dates)

    def test_search_invalid_date_range_raises(self):
        service = make_service()
        with pytest.raises(ValueError, match="date_from"):
            service.search_events(date_from=FUTURE_DATE_3, date_to=FUTURE_DATE)

    def test_search_keyword_no_match_returns_empty(self):
        service = make_service()
        self._setup_events(service)
        results = service.search_events(keyword="xyznotaword")
        assert results == []