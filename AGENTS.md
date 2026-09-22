# AGENTS.md

## Purpose

This file contains the operating rules for AI coding agents working in the Orbit repository.

Orbit is a personal AI planning assistant. Its product principle is:

> **Tell me what I want to accomplish. You figure out when and how.**

The agent should help implement Orbit without silently changing its product requirements or architecture.

## Before changing code

1. Inspect the relevant files and surrounding architecture.
2. Read the relevant documentation in `docs/`.
3. Check whether the requested behaviour already has a product or architectural decision.
4. State the proposed approach before making a non-trivial change.
5. Prefer the smallest implementation that proves the requirement.
6. Do not modify unrelated code.

For ambiguous requirements, ask the user. Do not invent important product decisions.

## Product rules

### User defines scope

Orbit only manages information the user has explicitly provided or explicitly allowed it to access.

Do not assume unrelated personal information.

### User defines priorities

Priorities are part of the user's current planning context.

Never invent a permanent hierarchy of the user's life.

If important priorities conflict and the system cannot resolve the conflict from explicit context, ask the user.

### AI plans; user controls

The AI is responsible for planning and proposing actions.

The user remains responsible for approving important actions.

A user must be able to:

- approve
- modify
- reject
- override

AI proposals where the product flow supports those actions.

### Ask rather than assume

Never silently invent important:

- deadlines
- durations
- priorities
- goals
- constraints

If missing information is necessary for a safe/useful decision, request clarification.

### Progress

Initially, Orbit must not assume that scheduling an activity means it was completed.

Progress is user-reported.

Supported outcomes include:

- completed
- partially completed
- not completed
- actual time spent
- relevant notes

## Autonomy

Orbit uses a risk/priority-based autonomy model.

```text
Low-risk / low-priority
        ↓
More autonomy

Important / high-priority
        ↓
More approval
```

Initial rule:

> **When in doubt, ask.**

The AI must not silently:

- change goals
- change priorities
- make significant calendar changes
- perform important actions without the appropriate approval

The autonomy model can evolve as reliability and trust improve.

## Architecture rules

- The Orbit database is the source of truth.
- Google Calendar and Google Tasks are integrations/execution surfaces.
- Keep the domain model independent from external service schemas.
- Keep planning logic separate from integration/tool execution.
- Do not make the core application depend directly on one external productivity provider.
- Prefer explicit interfaces between domain logic and integrations.
- Avoid premature multi-agent architectures.
- Do not add a complex Goal → Activity → Task hierarchy unless a documented product decision requires it.

## Current stack

- Backend: Python + FastAPI
- Frontend: React + TypeScript
- Desktop: Tauri
- Database: PostgreSQL
- Initial integrations: Google Calendar + Google Tasks

## MVP task model

The MVP should keep the task representation simple.

A task currently represents:

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

Do not add unnecessary fields merely because they might be useful later.

## Code quality

- Prefer readable code over clever code.
- Keep functions and modules focused.
- Use types/models at system boundaries.
- Validate external input.
- Handle integration failures explicitly.
- Do not swallow errors silently.
- Add tests for meaningful behaviour.
- Preserve existing functionality unless the change explicitly replaces it.
- Avoid unnecessary dependencies.

## Agent workflow

For non-trivial work:

```text
1. Understand
2. Plan
3. Implement
4. Test
5. Review
6. Report
```

### Understand

Inspect the relevant repository files and documentation.

### Plan

Explain:

- what will change
- why
- relevant files
- risks
- testing approach

### Implement

Make the smallest reasonable change.

### Test

Run the most relevant tests/checks available.

### Review

Look for:

- regressions
- incorrect assumptions
- security problems
- unnecessary complexity
- documentation inconsistencies

### Report

Summarise:

- changes made
- tests run
- important decisions
- remaining risks

## Documentation rules

When implementation changes the current architecture or product behaviour:

1. Update the relevant `docs/` file.
2. Record significant decisions in `docs/decisions.md`.
3. Do not rewrite historical development notes as if they were current requirements.
4. Keep `README.md` focused on the current state and how to understand/use the project.

## Git safety

Before large or risky changes:

- inspect `git status`
- avoid overwriting unrelated user work
- keep changes reviewable
- do not create commits unless explicitly requested

Never use destructive Git commands to discard user work unless explicitly instructed.

## Definition of done

A task is not complete merely because code was written.

Where applicable, completion means:

- requirement implemented
- relevant tests pass
- errors are handled
- documentation reflects meaningful changes
- no unrelated files were modified
- behaviour matches Orbit's product principles
