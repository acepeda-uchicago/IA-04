# Sprint Review — IA-04: Implementation Sprint
**Author:** Alec Cepeda (acepeda)
**Course:** MPCS 51200 — Introduction to Software Engineering


## Demo Summary

The sprint delivered a fully working Python service layer for the Campus Event Management Platform. A stakeholder interacting with the system through code would be able to do the following:

**Create an Event.** An event organizer can create a new event by providing a title, description, date, venue, and capacity. The system validates all inputs before accepting the event. Should any of these inputs be in violation the system will reject it. This includes errors from past dates, empty required fields, and non-positive capacities, raising descriptive errors in each case. Successfully created events are assigned a unique ID and stored.

**Register for an Event.** A user can register for any active event. The system enforces a hard capacity limit (registrations below the limit are marked confirmed, and any registration submitted once the event is full is automatically placed on a waitlist). The system also prevents a user from registering for the same event twice. If a confirmed registrant later cancels, the first person on the waitlist is automatically promoted to confirmed.

**Search Events (Elective).** Users can search for active events using any combination of a keyword (matched against title and description), a date range, and a venue. Filters are combined with AND logic, and results are always returned sorted by date. Cancelled events never appear in search results.

All features are covered by 38 automated tests that can be run via pytest.


## Completed vs. Planned

| Story | Status | Notes |
|-------|----------|-------|
| Create Event | Planned and Completed | All validations implemented |
| Register for Event | Planned and Completed | Capacity, waitlist, and duplicate prevention all working |
| Unit Tests (10+ minimum) | Planned and Completed | 38 tests written and passing |
| Search Events (elective) | Planned and Completed | Keyword, date range, and venue filters all working |
| Cancel Registration | Not originally planned but Completed | Not originally planned but a knock-on requirement of implementing waitlist promotion logic |

No planned stories were left incomplete. cancel_registration was not in the original sprint plan but was implemented because waitlist promotion requires it (a registrant must be able to free their slot before the waitlist can advance). 

One aspect that I didn't strictly define in my sprint plan was how I was going to save data products. In the last assignment data storage was defined as a SQL database and for this implementation I only used a python dictionary. Implementing SQL seemed out of scope for an initial iteration but could be added in the future. 


## Technical Decisions

**1. Custom exceptions.**
I utilized two custom exception classes: EventNotFoundError and DuplicateRegistrationError. Instead of just raising a ValueError for everything I felt this better represented what was actually failing validation and made writing understandable tests far easier. For instance, a pytest entry checking pytest.raises(EventNotFoundError) does not require any comments to express what is being tested while just checking pytest.raises(ValueError) would not be as clear as to what the test is checking as many entries utilize ValueErrors. 


**2. Date input accepted as strings.**
In many places in the code a global date string format was defined as `"YYYY-MM-DDTHH:MM:SS"`. The service layer accepts this string entry for the date rather than requiring the caller to pass a python datetime object. I chose this as the conversion from string to datetime interally seemed trivial and allowed the calling interface to mirrors what a real API layer would receive (which wasn't implemented here). The parsing and validation logic was centralized in a single private _parse_date method. 

**3. Waitlist managed by registration timestamp, not insertion order.**
When a confirmed slot opens, the first waitlisted user is determined by their registered_at timestamp rather than relying on dict insertion order. This is more explicit, seems more fair, and direcly mirrors the logic that would would be required in future migration to a database where insertion order may not be guaranteed.

**4. Python dictionary for data storage.**
This was already alluded to in 'Completed vs. Planned' but the implementation was limited to using a python dictionary for data storage versus the original plan for using an SQL database like SQLite3 or MySQL. This was done purely to limit the scope of the initial sprint. During this sprint I wanted to stress creating regression tests (38 created in total) for core functionality and the story points associated with implementing a working SQL implementation would have been too much for this initial sprint. I did try to modularize the code in such a way that implementation could be added in the future.  

## Examples

### Create an Event

```python
from event_platform.services import EventService

service = EventService()

event = service.create_event(
    title="Tech Talk",
    description="An introduction to distributed systems.",
    date="2026-04-15T00:00:00",
    duration=1.0,
    venue="Crerar Lab",
    capacity=2,
)
print(event)
# Event(id=1, title='Tech Talk', date='2026-04-15T00:00:00', venue='Crerar Lab', capacity=2, status='active')
```

### Validation — past date rejected

```python
service.create_event(
    title="Old Event",
    description="This already happened.",
    date="2024-01-01T00:00:00",
    duration=1.0,
    venue="Room 101",
    capacity=10,
)
# ValueError: Event date 2024-01-01T00:00:00 is in the past.
```

### Register for an Event — confirmed and waitlisted

```python
r1 = service.register(event_id=event.id, user_id="user_1")
print(r1)
# Registration(id=1, event_id=1, user_id='user_1', status='confirmed')

r2 = service.register(event_id=event.id, user_id="user_2")
print(r2)
# Registration(id=2, event_id=1, user_id='user_2', status='confirmed')

r3 = service.register(event_id=event.id, user_id="user_3")
print(r3)
# Registration(id=3, event_id=1, user_id='user_3', status='waitlisted')
```

### Waitlist promotion on cancellation

```python
service.cancel_registration(event_id=event.id, user_id="user_1")

regs = service.get_registrations_for_event(event.id)
for r in regs:
    print(r)
# Registration(id=1, event_id=1, user_id='user_1', status='cancelled')
# Registration(id=2, event_id=1, user_id='user_2', status='confirmed')
# Registration(id=3, event_id=1, user_id='user_3', status='confirmed')  ← promoted
```

### Duplicate registration rejected

```python
service.register(event_id=event.id, user_id="user_2")
# DuplicateRegistrationError: User 'user_2' is already registered for event 1.
```

### Search Events

```python
service2 = EventService()
service2.create_event("Python Workshop", "Intro to Python.", "2026-05-01T00:00:00", "Crerar Lab", 30)
service2.create_event("Career Fair", "Meet top recruiters.", "2026-06-15T00:00:00", "Main Hall", 100)
service2.create_event("Spring Festival", "Campus-wide celebration.", "2026-07-04T00:00:00", "Main Quad", 500)

# Keyword search
results = service2.search_events(keyword="Python")
print([e.title for e in results])
# ['Python Workshop']

# Venue search
results = service2.search_events(venue="Main")
print([e.title for e in results])
# ['Career Fair', 'Spring Festival']

# Date range
results = service2.search_events(date_from="2026-06-01T00:00:00", date_to="2026-07-01T00:00:00")
print([e.title for e in results])
# ['Career Fair']

# Combined filters
results = service2.search_events(keyword="recruiters", venue="Main Hall")
print([e.title for e in results])
# ['Career Fair']
```