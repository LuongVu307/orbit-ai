# Product

## Vision

> **Tell me what I want to accomplish. You figure out when and how.**

Orbit is a personal AI planning assistant that turns intentions and goals into realistic tasks, schedules, and adaptive plans.

The user provides what they want to achieve and the constraints that matter. Orbit determines how to organise the work while preserving user control.

## Primary user

The initial product is designed for a university student with multiple simultaneous goals and projects who already uses calendar/task software but wants to automate planning, reminding, and replanning.

The MVP is a personal internal tool. Architecture should avoid unnecessary multi-user complexity while not preventing future expansion.

## Jobs to be done

### Capture

When I think of something I need to do, I want to tell the AI immediately so I do not have to remember or manually organise it.

### Decide

When I have several things to do, I want the AI to determine what I should work on and when.

### Schedule

When I know what I need to accomplish, I want the AI to fit it into available time.

### Plan

When I have a larger goal, I want the AI to turn it into a realistic plan.

### Adapt

When reality differs from the plan, I want the AI to adjust the plan rather than making me rebuild it.

## Product principles

1. User defines scope.
2. User defines priorities.
3. AI handles planning.
4. AI proposes; user controls.
5. Progress initially requires user feedback.
6. Autonomy increases gradually.
7. AI should be proactive without becoming intrusive.

## Long-term stages

1. **Remember & Remind**
2. **Plan My Day**
3. **Plan My Week**
4. **Manage My Goals**

The MVP should prove the first stage before attempting the later stages.

## MVP

The MVP should allow a user to express an intention naturally and have Orbit:

1. understand it
2. gather relevant context
3. identify missing information
4. ask clarification questions when necessary
5. propose an action
6. receive approval/modification/rejection
7. execute the approved action
8. record the user's reported progress

## Example

User:

> I need to revise Dijkstra before Friday.

Orbit should identify that the deadline is known but duration and possibly priority are unknown.

If duration is necessary:

> How long do you expect this to take?

After receiving an estimate, Orbit can inspect the calendar and propose a suitable slot.

The user approves the proposal before the calendar is changed when approval is required.

Later, the user can report that the work took longer than expected. Orbit records the actual outcome for future planning.

## MVP scope

### Must have

- chat-based natural-language interaction
- task understanding
- relevant context
- calendar reading and scheduling
- internal task representation
- approval flow
- progress reporting
- basic proactive suggestions
- autonomy rules

### Explicitly deferred

- full goal management
- automatic goal decomposition
- complex milestones
- full weekly planning
- sophisticated daily optimisation
- continuous autonomous replanning
- automatic progress verification
- automatic learning of all personal preferences
- voice
- mobile
- multiple specialised agents
- large-scale integrations
- public multi-user product
- advanced analytics
- full autonomy

## User control

Orbit must allow the user to approve, modify, reject, and override proposals.

Important actions require appropriate approval.

The AI must not silently change user goals or priorities.

## Success

The core hypothesis is:

> If I can tell the AI what I want to accomplish naturally, and it can understand my intention, consider relevant context, propose an appropriate action and execute it with my approval, then it can reduce the mental effort required to manage my productivity.

The north-star concept is:

> **Meaningful goal progress per unit of planning effort.**
