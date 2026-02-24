# Sprint Plan — IA-04: Implementation Sprint
**Author:** Alec Cepeda (acepeda)  
**Course:** MPCS 51200 — Introduction to Software Engineering  
**Sprint Duration:** 2 weeks (Thu Mar 5, 2026 6:00pm)

---
## Sprint Goal

Deliver a working Python service layer that allows an event organizer to create an event and register users for it — enforcing all core business rules — and expose event search functionality so students can discover events by keyword, date range, or venue.

---

## Selected Stories and Story Point Estimates


| Story | Description | Estimate | Rationale |
|-------|----------|-----------|------------|
| Create Event | Service method to create an event with title, description, date/time, venue, and capacity. Validates required fields, rejects past dates, and enforces positive capacity. | 3 | Fairly straighforward method but requires several steps of input validation |
| Register for Event | Service method to register a user for an event. Enforces capacity limits (waitlist when full) and prevents duplicate registrations. | 5 | Most complex story — several business rules (capacity, waitlist promotion, duplicate prevention, etc) that interact with each other |
| Unit Tests | Minimum 10 meaningful tests covering happy paths, edge cases, and error conditions for the above features. | 2 | Writing tests is relatively fast once the service layer is in place, but reaching full coverage of edge cases will take moderate effort |
| Search Events | Find events by keyword (matching title or description), date range, and/or venue. Returns sorted results. | 3 | Filtering across multiple optional criteria is moderately complex, need to handle combinations of filters cleanly |
| **Total** | **13** | |

---

## Elective Justification

**Selected feature: Search Events**

In IA-02, FR-04 (Event Discoverability) and US-03 ("As a student, I want to search for events by keyword so that I can quickly find relevant events") were both given high priority, and reflect that discoverability is central to student adoption of the platform. The product vision in IA-01 explicitly ties success to students choosing the system voluntarily which requires them to be able to find events easily.

In TA-03, the `GET /events` API endpoint was designed with filtering by date, category, and location, indicating that search was already considered a core aspect of the software. Implementing search in the service layer directly supports that design intent and creates a natural foundation for the REST API layer if that is added in the future.

---

## Definition of Done

A story is considered **done** when all of the following are true:

1. Functionality: The feature behaves correctly for all specified business rules and acceptance criteria.
2. Error handling: Invalid inputs raise appropriate exceptions.  
3. Tests passing: All related unit tests pass when run via `pytest` with no warnings suppressed.
4. Test coverage: Both happy path and at least one edge case or error condition are covered by tests for each business rule.
5. Code quality:  Business logic lives in the service layer, not in models or test files. Methods have clear documentation. 
---

## Notes & Risks
- The TA-03 domain model (Event, User, Registration, Venue entities) will guide the model classes, but the full complexity (Organization, ApprovalRecord, etc.) is out of scope for this sprint.