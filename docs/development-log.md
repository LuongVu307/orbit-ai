# Development Log

This document is intentionally for **historical development context**, not current product requirements.

Use it to record short entries about:

- what was built
- what was learned
- what failed
- important decisions
- experiments
- observations from real use

## Entry template

```md
## YYYY-MM-DD — Short title

### What changed

- ...

### What I learned

- ...

### Decisions

- ...

### Problems

- ...

### Next

- ...
```

## Existing project context

The project has already gone through product-definition work establishing:

- the product vision
- primary jobs-to-be-done
- desired workflow
- MVP scope
- autonomy principles
- data ownership
- initial integrations
- success metrics
- development roadmap

The current roadmap identifies **Core Agent** as in progress, with **Design Domain Model** as an in-progress infrastructure task.

## Important distinction

Historical notes may contain ideas that were later rejected or deferred.

AI agents should use:

1. `README.md` for current project orientation
2. `docs/product.md` for current product requirements
3. `docs/architecture.md` for current architecture
4. `docs/decisions.md` for established decisions
5. this file for historical context

Do not treat an old development-log idea as a current requirement unless it is reflected in the current documentation.

## 2026-09-22 — Stateful task feedback loop

### What changed

- Added an in-memory draft conversation that gathers required task information
  across messages before creating a proposal.
- Kept task persistence behind explicit confirmation.

### Decisions

- Conversation state remains in memory for this initial implementation.

### Testing

- Before running backend commands, activate the project environment with
  `conda activate orbit-ai`.

## 2026-09-23 — Desktop feedback-loop UI

### What changed

- Replaced the starter desktop screen with a chat-first Tauri UI for
  clarification, proposal review, approval, cancellation, and modification.
- Allowed a user message during confirmation to update the existing draft and
  return it for renewed approval.
- Added current-date context for local LLM deadline extraction.
- Isolated database tests in rollback-only transactions so tests cannot delete
  or persist production task data.

### Testing

- Verified the live API can reach PostgreSQL and read persisted tasks.
- Verified a live draft can be clarified, modified, and cancelled without
  creating a task.
- Backend tests, desktop lint, and the desktop production build pass.
