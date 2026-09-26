---
schema_version: 1
task_id: ORBIT-0003
title: Add one-command local Orbit startup
status: completed
---

## Objective

Provide one local command that prepares Orbit's development dependencies,
applies database migrations, starts missing owned services, verifies health,
and launches the native desktop application.

## Motivation

The current multi-terminal startup is easy to perform incompletely. In
particular, a running backend with an outdated development database produced a
generic desktop fetch failure after persistent conversations were introduced.

## Acceptance criteria

- npm run desktop checks required local tools and starts the complete stack.
- PostgreSQL is started and awaited before database access.
- Development migrations are applied before FastAPI starts.
- Ollama and the configured gemma3 model are verified.
- An existing healthy Orbit API is reused; otherwise an owned API process is
  started and awaited.
- Cargo uses a local Windows cache that avoids the secondary-filesystem unpack
  failure.
- Only processes started by the launcher are stopped during cleanup.
- Startup failures identify the failing component and preserve useful logs.
- The desktop presents a useful message when the local API is unreachable.

## Non-goals

- Production deployment orchestration.
- Installing Docker, Conda, Rust, Node, Ollama, or downloading model weights.
- Stopping PostgreSQL or unrelated pre-existing processes.
- Authentication, integrations, or model-quality changes.

## Constraints and relevant decisions

- Keep the workflow local to Windows and the existing development stack.
- Never treat a process merely occupying a required port as an Orbit service.
- Do not stop any service the launcher did not start.
- Preserve the user's existing uncommitted desktop-launcher work.

## Affected product behaviour

Product planning behaviour is unchanged. Local startup becomes deterministic,
and network failures in the desktop receive a clearer explanation.

## Validation requirements

- Run the launcher while PostgreSQL, Ollama, and FastAPI are already healthy.
- Confirm it reaches Tauri and does not stop pre-existing services on exit.
- Run the mandatory All validation scope.
- Review the final diff for correctness and unsafe process handling.

## Approval questions

None. The user approved the complete launcher plan on 2026-09-26.

## Approved implementation plan

Add a full-stack PowerShell orchestrator, retain the focused Tauri environment
script, route npm run desktop through the orchestrator, improve desktop network
errors, and document startup, migrations, ownership, and cleanup.

## Final handoff notes

Changed behavior:

- `npm run desktop` now prepares PostgreSQL, applies development migrations,
  verifies Ollama and `gemma3`, starts FastAPI when needed, and launches Tauri.
- Existing healthy Ollama and Orbit API services are reused.
- Owned FastAPI, Ollama, Tauri, Vite, and desktop processes are cleaned up;
  pre-existing services and PostgreSQL are left running.
- Cargo uses `%LOCALAPPDATA%\orbit-cargo`, avoiding crate-unpack failures on
  the repository filesystem.
- The desktop now explains when the local API is unavailable.

Validation:

- Live one-command startup applied current migrations, started an owned API,
  launched Vite on port 5173, compiled Tauri, and opened the native app.
- A live model request reached `ready_for_confirmation`; its disposable draft
  was cancelled without creating a task.
- Ctrl+C cleanup removed owned desktop, Vite, Tauri, and FastAPI processes
  while leaving PostgreSQL and the pre-existing Ollama service running.
- Mandatory `All` validation passed: 13 backend tests, desktop lint/build, and
  `cargo check --locked`.

Remaining risks:

- The launcher is Windows-specific and intended only for local development.
- FastAPI runs without auto-reload under the orchestrator; backend code changes
  require restarting `npm run desktop`.
- Cargo still emits non-blocking hard-link fallback warnings for incremental
  build artifacts under the repository's `E:` filesystem.
