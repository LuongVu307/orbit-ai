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

## 2026-09-24 — Local agentic development workflow

### What changed

- Added versioned task, review, and handoff templates.
- Added one non-rewriting validator for backend, desktop, and Tauri checks.
- Isolated backend tests to a database whose name ends in `_test`.
- Separated deterministic local-LLM tests from advisory live-model evaluation.

### Testing

- The mandatory `All` validation scope passed with 12 backend tests, desktop
  lint/build, and `cargo check --locked`.
- The advisory `gemma3` evaluation passed 3 of 6 cases; model-quality failures
  remain non-blocking while the evaluation suite is advisory.

### Known limitation

- The backend still uses one process-global draft conversation. This is an
  explicitly accepted constraint for the current single-user,
  single-conversation prototype and must be replaced with session-scoped
  persistence before concurrent or multi-user operation.

## 2026-09-25 — Persistent draft conversations

### What changed

- Replaced process-global draft state with PostgreSQL-backed conversations.
- Added client-held conversation UUIDs and restoration of unfinished drafts.
- Made the agent stateless with respect to conversation lifecycle state.
- Made approval operate on the stored draft with row locking and idempotent,
  atomic task creation.
- Added desktop persistence of the active conversation UUID without storing
  full chat transcripts.

### Decisions

- A conversation UUID correlates local state but is not authentication.
- Orbit remains single-user and local-use until an identity and authorization
  model is explicitly introduced.

### Testing

- Added coverage for draft persistence, restoration, isolation, cancellation,
  and repeated approval.
- The mandatory `All` validation scope passed with 13 backend tests, desktop
  lint/build, and `cargo check --locked`.
- Bugbot's duplicate React Strict Mode restoration finding was fixed with an
  idempotence guard. Security Review found no issues within the current threat
  model.

## 2026-09-26 — One-command local startup

### What changed

- Routed `npm run desktop` through a full local-stack launcher.
- Added prerequisite checks, PostgreSQL readiness, automatic development
  migrations, Ollama/model verification, FastAPI health checks, and Tauri
  startup.
- Moved Cargo's registry cache to `%LOCALAPPDATA%\orbit-cargo` to avoid crate
  unpack failures on the repository filesystem.
- Added exact service/port checks and cleanup limited to launcher-owned
  processes.
- Replaced the desktop's generic network failure with an actionable local API
  message.

### Testing

- Verified startup with PostgreSQL and Ollama already running and FastAPI
  stopped; the launcher applied migrations, started FastAPI, and opened Tauri.
- Verified a live `gemma3` task request and cancelled its disposable draft.
- Verified Ctrl+C removed only owned desktop/API processes and left PostgreSQL
  and pre-existing Ollama running.
- The mandatory `All` validation scope passed with 13 backend tests, desktop
  lint/build, and `cargo check --locked`.

### Next

- Begin `ORBIT-0004`: expand real-world intent evaluation and harden the local
  model prompt before adding calendar execution.

## 2026-09-26 — Evidence-aware intent reliability

### What changed

- Added a versioned 36-case corpus covering complete tasks, partial follow-ups,
  informal wording, typos, ambiguity, conflicts, multiple tasks, unsupported
  requests, and prohibited inference.
- Preserved prompt v1 as a baseline and added prompt v2 with source evidence,
  explicit ambiguity signals, and an Ollama JSON schema.
- Added deterministic validation that accepts only user-supported fields,
  resolves supported dates and times outside the model, and asks targeted
  clarification questions.
- Kept extraction evidence outside the task domain and shared the same prompt,
  parser, and validator between production and advisory evaluation.

### Testing

- Prompt v1 passed 8 of 37 checks (21.6%) and produced 17 prohibited
  inferences against the expanded corpus and malformed-output adapter case.
- Prompt v2 passed 29 of 37 checks (78.4%) and produced zero prohibited
  inferences. Priority passed 30/30 field checks and deadline passed 29/30.
- The deterministic backend suite passes with 44 tests, including regression
  coverage for independent multi-task detection, daylight-saving transitions,
  confirmation-state preservation, bounded relative dates, unlisted second
  task verbs, and mixed conflicting date expressions.
- Agent messages are limited to 4,000 characters, and conjunction validation
  scans each clause once. The review stress case dropped from seconds to about
  0.02 seconds in a direct local check.
- Final independent Bugbot and security reviews found no actionable issues.

### Known limitations

- `gemma3` can still classify short valid tasks as unsupported and can omit or
  shorten explicit context. Those failures are conservative: rejected data is
  not merged into a draft.
- Substantial clauses joined by `and` or `then` are conservatively treated as
  multiple tasks unless they match a small set of established compound phrases.
  This can ask for clarification on some coordinated-object wording, but avoids
  silently collapsing two actions into one task.
- The live model evaluation is advisory because local-model output and runtime
  vary. Deterministic validation remains the required build gate.

### Next

- Use real personal conversations to extend the corpus before changing models
  or adding broader language heuristics.
- Plan the next Core Agent increment separately before starting calendar
  execution work.
