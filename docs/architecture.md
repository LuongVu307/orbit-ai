# Architecture

## Status

This document describes the intended MVP architecture derived from the current product definition. It should be updated as implementation decisions are made.

## Architectural goal

Separate:

1. understanding user intent
2. storing Orbit's domain state
3. planning/proposing actions
4. executing actions through integrations
5. collecting progress

The architecture should allow external productivity services to change without rewriting Orbit's core domain logic.

## High-level system

```text
                  User
                   │
                   ↓
             Chat Interface
                   │
                   ↓
             API / Backend
                   │
          ┌────────┴────────┐
          ↓                 ↓
      AI Agent          Domain Services
          │                 │
          └────────┬────────┘
                   ↓
              Orbit DB
          (source of truth)
                   │
          ┌────────┴─────────┐
          ↓                  ↓
 Google Calendar       Google Tasks
   integration           integration
          │                  │
          └────────┬─────────┘
                   ↓
               External
              execution
```

## Application stack

### Backend

Python + FastAPI.

Responsibilities:

- API endpoints
- orchestration
- domain/application services
- persistence
- AI-agent integration
- tool/integration boundaries

### Frontend

React + TypeScript.

The MVP interface is chat-first.

The interface should prioritise:

- fast input
- clear AI responses
- proposed actions
- approval
- modification
- rejection
- progress reporting

A sophisticated dashboard or calendar UI is not required for the initial MVP.

### Desktop

Tauri is the intended desktop shell.

### Database

PostgreSQL is the intended persistent store.

Orbit's database is the source of truth.

## Domain boundaries

A useful conceptual separation is:

```text
domain/
    Core concepts and business rules

services/
    Application workflows

agent/
    AI reasoning/orchestration

tools/
    Controlled actions available to the agent

integrations/
    Google Calendar / Google Tasks adapters

database/
    Persistence implementation

api/
    External HTTP interface
```

The exact package structure may evolve as implementation progresses.

## Source of truth

Orbit owns the canonical representation of:

- tasks
- relevant goals/context
- priorities
- planning state
- progress
- approval state
- links to external entities

External systems are not the canonical representation of Orbit's domain.

Conceptually:

```text
                 Orbit DB
               /                        /                 Calendar adapter    Tasks adapter
            ↓                  ↓
     Google Calendar     Google Tasks
```

## Task model

For the MVP, keep the task model deliberately simple:

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

The MVP should not introduce separate Goal → Activity → Task entities unless later product requirements justify them.

## Agent workflow

The core workflow is:

```text
User intention
      ↓
Understand intention
      ↓
Gather relevant context
      ↓
Identify missing information
      ↓
Ask user when necessary
      ↓
Create proposal
      ↓
Approval / modification / rejection
      ↓
Execute approved action
      ↓
Record progress
```

The AI should distinguish between:

```text
User-provided facts
        vs
Unknown information
        vs
AI-generated proposal
```

These should not be treated as equivalent.

### Intent extraction boundary

Local-model output is untrusted input. The model extracts candidate task facts,
quotes the user text supporting each fact, and reports ambiguity. A
deterministic validator then accepts only evidence present in the user's
message. It resolves supported date and time expressions itself and discards
unsupported deadlines, priorities, descriptions, and titles before anything is
merged into the draft conversation.

```text
User message
     ↓
Untrusted structured extraction + quoted evidence
     ↓
Deterministic evidence and ambiguity validation
     ↓
Validated facts or a specific clarification
     ↓
Draft conversation
```

The production path and the advisory model-evaluation path share the same
prompt, parser, and validator. Versioned evaluation cases use a fixed clock so
relative-date results can be compared across prompt versions without making
live-model quality a mandatory build gate.

### Draft conversations

While required task information is being gathered, the agent keeps an
in-progress `DraftTask` in a PostgreSQL-backed draft conversation. Each
conversation has a UUID held by the desktop client. Each message is extracted
into facts and merged into that conversation's draft. The agent—not the
LLM—checks whether required fields are present and either requests the missing
fields or creates a proposal.

Draft persistence does not make a draft an approved task. On approval, the
backend locks and reads the stored conversation, creates the task, and marks
the conversation executed in one transaction. Repeated approval returns the
existing task rather than creating a duplicate.

The UUID correlates and isolates local conversation state; it is not an
authentication or authorization boundary. Orbit remains a single-user product
at this stage. Full chat transcripts are not persisted.

## Approval boundary

The AI may reason about an action without executing it.

Execution should happen through controlled tools/integrations.

Conceptually:

```text
AI reasoning
     ↓
Action proposal
     ↓
Approval policy
     ↓
User approval when required
     ↓
Tool execution
     ↓
Result
     ↓
Persist result
```

This makes approval auditable and reduces accidental external actions.

## Autonomy

Initial autonomy is risk/priority based.

```text
Low-risk / low-priority
        ↓
Less intervention

High-priority / important
        ↓
Explicit approval
```

Unknown or ambiguous important decisions should result in clarification.

## Calendar integration

The calendar is an execution surface.

Required MVP capabilities:

- read events
- find available time
- create events
- modify events
- move events
- delete events
- detect conflicts

Orbit should translate its internal model into calendar-specific operations through an adapter rather than coupling domain logic directly to Google Calendar's schema.

## Tasks integration

Google Tasks is an initial integration.

Orbit should maintain its own task representation and use Google Tasks as an external productivity surface where appropriate.

## Progress

Initially:

```text
Scheduled
   ↓
User reports outcome
   ↓
Orbit records:
- completion state
- actual time
- notes
   ↓
Future planning can use the history
```

Scheduling must not be treated as proof of completion.

## Proactive behaviour

Orbit may identify situations where an action could be useful, for example when a deadline is approaching and the work remains unscheduled.

Initial principle:

> Suggest rather than silently change important plans.

## Reliability requirements

Integration failures should be explicit.

For example:

```text
Proposal
   ↓
Execution attempt
   ↓
Success ─────→ persist result
   │
   └── Failure → communicate failure
                 preserve state
                 allow retry/recovery
```

Never report a calendar/task action as successful unless the external operation actually succeeded.

## Future evolution

Later stages can add:

- day planning
- week planning
- goal management
- richer memory
- learned duration estimates
- automatic progress verification
- more integrations
- greater autonomy

These should extend the architecture rather than forcing the MVP to implement them prematurely.
