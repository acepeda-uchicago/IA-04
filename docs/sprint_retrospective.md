# Sprint Retrospective — IA-04: Implementation Sprint
**Author:** Alec Cepeda (acepeda)
**Course:** MPCS 51200 — Introduction to Software Engineering


## What Went Well

- Building models.py first and focusing on getting Event, Registration, and the status enums right before touching the service layer meant the service methods had a stable foundation to build on. There were no cases where a model change forced a rewrite of service logic.

- Writing tests alongside implementation caught real bugs early and helped for refactoring. Since I was writing tests as I was working through the business logic I was able to quickly test new features as I implemented them. Additionally, as I got close to the end of the sprint and wanted to refactor some of my business logic code I could do so with confidence that my automated tests would catch any errors I made.

- Custom exceptions made the test suite much more readable. Using EventNotFoundError and DuplicateRegistrationError instead of generic ValueError for every error case made pytest.raises(...) assertions clear and specific. It also made it easier to follow the logic in my own code during private testing. 


## What Could Be Improved

- When creating my pytest tests several of the test classes has very similar events created with dummy values. I am sure there was a more concise way to do this if I was more familiar with pytest and in future sprints I might explore this in order to make the tests more readable in the future. 


- There were a couple of times where I started writing code before really thinking through how I wanted classes to interact. For example, the is_full() method was designed into the Event model because I thought I would have to often check if an event had met the capacity limit but I never ended up using it. Instead the capacity check ended up living entirely in _confirmed_count() in the service layer. Had I more rigirously defined the methods I wanted to use this waste of work wouldn't have happened. I left this in the code since it may be useful in the future but has no function currently. 

- I did not create any full integration tests that walk through creation → registration → fill to capacity → cancellation → promotion. I found that after exhaustively creating unit tests I had reached the "time-box" limit I had defined for this task. This should be something that is implemented in the future. 

---

## What Surprised Me

- When estimating I thought one of the hardest features would be the waitlist promotion feature but in reality that was only a few lines. What took longer was thinking through all the cases like what happens when a waitlisted user cancels (no promotion should occur), and what happens when a user cancels and then tries to re-register. Writing tests for these before implementing them made the edge cases apparent early. 

- I was surprised how much time I spent on the tests. At first I thought most of my time would be spent in the implementation but quickly I learned that iterative testing of my implementation was necessary and I needed to be writing tests **as** I was creating features. My first couple tests were not robust and had bugs which lead me to waste a ton of time debugging my implementation unecessarily. I realized the importance of investing in creating quality tests early and how that actually ended up being a far larger portion of my success than a clean initial implementation. 


---

## Velocity Reflection

| Story | Original Estimated Points | Post-Sprint Reflected Points| Notes |
|-------|-----------------|---------------|-------|
| Create Event | 3 | 3 | Estimate was accurate. Validation logic was straightforward once the model was in place. |
| Register for Event | 5 | 4 | Estimate slightly overshot actual work. The waitlist promotion added logic complexity but was actually easier than first imagined. |
| Unit Tests | 2 | 4 | Underestimated. Writing 38 meaningful tests took significantly longer than a 2 point task implied. Edge case identification was the slow part. |
| Search Events | 3 | 2 | Slightly overestimated. The filtering logic was fairly simple to implement. |

The main takeaway is that testing was underestimated relative to implementation. A 2 point estimate for tests implied it would be the easiest part of the sprint, but it took as long as any individual feature. 

---

## Design vs. Reality

The TA-03 domain model held up well at the conceptual level. Event, Registration, and the status enumerations mapped directly to the implementation Several simplifications were made deliberately:

- User is a very basic representation of the original plan. The TA-03 model had Student, EventOrganizer, Administrator, and FacultyAdvisor all inheriting from a base User class. For this sprint, User is a minimal dataclass and these specializations are not represented. Role-based logic, including the approval system, was deemed out of scope.

- Organization, ApprovalRecord, Venue, and Notification were all dropped as they were out of scope for this first sprint. None of these were required by the sprint stories.

- Venue is currently only a string. In TA-03, Venue was its own entity that was connected to the Facilities API. In this implementation, venue is just a string field on Event.This decision was made because this was a service-layer sprint, external API integrations are out of scope and therefore at this point only a string field is necessary. 

- Since the approval process was out of scope some flagging large events, late events, or events with alcohol was deferred to a later sprint.