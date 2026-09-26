# Agentic Development Workflow

## Purpose

Orbit uses a local, human-gated development pipeline. A coding agent may plan, edit, test, and prepare a change for review. It may not commit, push, open a pull request, merge, change secrets, or publish anything on the user's behalf.

The workflow complements `AGENTS.md`; it does not replace the product or architecture decisions in `docs/`.

## Local application startup

After installing project dependencies, start the complete local application
from `apps/desktop`:

```powershell
npm.cmd run desktop
```

The launcher starts and awaits PostgreSQL, applies all pending Alembic
migrations to the local `orbit` database, verifies Ollama and `gemma3`, starts
FastAPI when necessary, and then starts Tauri. A healthy pre-existing Orbit API
or Ollama service is reused. On exit, only API or Ollama processes created by
the launcher are stopped; PostgreSQL and pre-existing services remain running.

Running migrations during startup is intentional. Application models and the
database schema must advance together, and `alembic upgrade head` is a no-op
when the database is current. The launcher does not install tools, packages, or
model weights.

## Task lifecycle

1. Copy `dev-workflow/templates/task-spec-v1.md` into `dev-workflow/tasks/`.
2. Complete every required section and resolve approval questions with the user.
3. Set `status` to `approved` only after the implementation plan is accepted.
4. Have one implementation agent make the smallest task-relevant change.
5. Run the mandatory validation scopes.
6. Give a fresh reviewer the task spec, approved plan, validation results, and final diff using `review-packet-v1.md`. Do not provide the implementation reasoning transcript.
7. Resolve objective findings and rerun affected checks. Return product ambiguity to the user.
8. Complete `handoff-v1.md`, set the task to `ready`, and leave commit and publication decisions to the user.

Supported task statuses are `proposed`, `awaiting-approval`, `approved`, `implementing`, `validating`, `review`, `ready`, `completed`, and `blocked`. The validator accepts only approved-through-completed implementation states.

## Mandatory validation

Run commands from the repository root in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate.ps1 -Scope Backend -TaskFile .\dev-workflow\tasks\TASK.md
powershell -ExecutionPolicy Bypass -File .\scripts\validate.ps1 -Scope Desktop -TaskFile .\dev-workflow\tasks\TASK.md
powershell -ExecutionPolicy Bypass -File .\scripts\validate.ps1 -Scope Tauri -TaskFile .\dev-workflow\tasks\TASK.md
powershell -ExecutionPolicy Bypass -File .\scripts\validate.ps1 -Scope All -TaskFile .\dev-workflow\tasks\TASK.md
```

The backend scope starts the Compose PostgreSQL service, creates `orbit_test` when needed, applies migrations to it, and runs pytest through the `orbit-ai` Conda environment. The test bootstrap refuses any database whose name does not end in `_test`.

The desktop scope copies tracked desktop inputs to a verified temporary directory, installs exactly the lockfile dependencies with `npm ci`, then runs lint and the production build there. This avoids rewriting `node_modules` or build output in the working tree and does not interrupt a running Vite process. The Tauri scope runs `cargo check --locked`; on Windows it uses an isolated cache under `%LOCALAPPDATA%\orbit-cargo`, discovers installed Visual Studio C++ build tools, and initializes their linker environment for the validation process.

Every scope returns a non-zero exit code on failure. The validator snapshots the content and index state of tracked files plus all non-ignored untracked files, then fails if a validation command changes them. Pre-existing changes are preserved. Ignored dependency, build, cache, and evaluation artifacts are outside this comparison by design.

## Advisory live-model evaluation

Mandatory tests use fakes and fixed clocks and never require Ollama. Run live checks separately:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\evaluate-ollama.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\evaluate-ollama.ps1 -Model gemma3
```

The command covers relative dates, named weekdays, missing deadlines, explicit priority, prohibited inference, and malformed-output handling. It records the model, prompt version, inputs, structured outputs, errors, and pass/fail results under `artifacts/evaluations/`. These reports are ignored by Git. A failed or unavailable live evaluation is reported honestly but does not alter the result of mandatory validation.

## Review and handoff

Bug review always checks correctness, regressions, acceptance criteria, architecture, error handling, complexity, and missing tests. Security review is required when a change touches input, dependencies, the database, external actions, permissions, secrets, or an approval boundary; otherwise it is explicitly marked not applicable.

The handoff distinguishes mandatory, optional, failed, and unrun checks. It also records resolved findings, remaining risks, branch and worktree state, and confirms that the agent did not commit or publish the change.

## Pilot and hardening

Pilot the workflow on one backend, one desktop, and one cross-layer task. Track first-pass validation success, review findings, rework cycles, unrelated-change rate, and human review time. Add automation only in response to observed friction; GitHub ingestion, CI, automatic PR creation, and autonomous merging remain deferred.
