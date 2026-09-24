# Domain Model

## MVP principle

The domain model should represent what Orbit needs to plan and execute tasks without prematurely modelling the entire long-term productivity system.

## Task

A Task represents something the user wants to accomplish.

Conceptually:

```text
Task
 ├── What
 ├── Context
 ├── Deadline
 ├── Duration
 ├── Priority
 ├── Status
 └── Related calendar event
```

### What

The core description of the activity.

Example:

> Revise Dijkstra

### Context

Relevant information needed to understand or perform the task.

### Deadline

When the task should be completed.

The MVP treats a deadline as important task information and should not invent one.

### Duration

Expected time required.

If duration is necessary for scheduling and unknown, Orbit should ask the user.

Orbit should eventually record both:

- estimated duration
- actual duration

This supports future planning improvements.

### Priority

The user's current planning priority.

Priority is contextual and user-defined.

Orbit must not silently infer a permanent life hierarchy.

### Status

The MVP should support at least:

```text
Not started
Completed
Partially completed
Not completed
```

The exact persistence representation can evolve.

### Related calendar event

A task may be associated with an external calendar event created for it.

The external event is not the task itself.

## Draft conversation

A Draft Conversation represents one task capture flow before execution.

```text
Draft Conversation
 ├── UUID
 ├── Draft task facts
 ├── Lifecycle status
 └── Executed task reference, when approved
```

It is durable so unfinished work can survive a restart, but it is not itself a
Task and does not imply approval. The desktop retains the active UUID. Chat
transcripts are outside the MVP model.

## Goals

Goals are part of the long-term product vision.

The MVP should avoid introducing a complex goal hierarchy.

Examples of long-term goals:

- reach 1400 Codeforces
- get an internship

A goal can provide context for tasks, but the MVP does not need to automatically decompose goals into complex milestone structures.

## Priorities

Priorities represent the user's current planning context.

Example:

```text
University  → High
Internship  → High
Personal AI → Medium
DSA         → Medium
Fitness     → Low
```

This is an example, not a hard-coded hierarchy.

## User-provided vs inferred data

Orbit should distinguish:

```text
Explicit user input
        ↓
Known fact
```

from:

```text
AI reasoning
        ↓
Proposal / estimate / interpretation
```

An AI estimate should not silently become a user fact.

## Proposal

A Proposal represents an action Orbit wants to take.

Conceptually:

```text
Proposal
 ├── intended action
 ├── reasoning/context
 ├── affected objects
 ├── required approval
 └── execution result
```

The exact schema should be designed during implementation.

## Approval

Approval represents the user's decision about a consequential proposal.

Possible outcomes:

```text
Approved
Modified
Rejected
```

Approval should be explicit where the autonomy policy requires it.

## Progress

Progress represents what actually happened.

At minimum:

```text
completion state
actual time spent
notes
```

The key distinction is:

```text
Plan ≠ Reality
```

Orbit should preserve actual outcomes so later planning can improve.

## External references

When Orbit interacts with an external system, store the relationship rather than making the external system the domain model.

Example:

```text
Orbit Task
    │
    └── external_calendar_event_id
```

This allows integrations to change independently.

## Future model

As the product evolves, the domain may gain:

- milestones
- goal plans
- recurring activities
- historical estimates
- richer progress records
- planning sessions
- learned preferences

These should be added only when validated by product needs.
