---
schema_version: 1
task_id: ORBIT-0001
title: Add the local agentic programming pipeline
status: completed
---

## Objective

Create a local, human-gated workflow that turns an approved task specification into a deterministic, independently reviewed, PR-ready change.

## Motivation

Orbit needs a repeatable development loop that benefits from coding agents without granting them commit, publication, merge, or product-policy authority.

## Acceptance criteria

- Versioned task, review, and handoff templates exist.
- One non-rewriting PowerShell validator supports Backend, Desktop, Tauri, and All scopes.
- Backend tests are forced onto an isolated database ending in `_test`.
- Deterministic tests do not require Ollama.
- A separate advisory command records live Ollama evaluation results.
- The workflow, commands, review gates, and human approval boundary are documented.

## Non-goals

- GitHub issue ingestion, CI, automatic branches, commits, pushes, PR creation, or merging.
- Concurrent implementation agents or autonomous backlog selection.
- Changes to Orbit's product task model or user-facing autonomy policy.

## Constraints and relevant decisions

- Follow `AGENTS.md` and the current product and architecture documentation.
- Preserve the Orbit database as source of truth and the planning/execution boundary.
- Keep the first workflow local to Windows, Conda, PostgreSQL, npm, Rust, and Ollama.
- Preserve all unrelated worktree changes.

## Affected product behaviour

Orbit's user-facing behavior is unchanged. Database configuration becomes environment-selectable, and local LLM calls gain an explicit timeout and testable clock.

## Validation requirements

- Run `All` scope against this task spec.
- Run deterministic malformed-output and fixed-clock tests without Ollama.
- Run the advisory Ollama suite if the local service and model are available; report it separately.
- Perform fresh bug and security review passes over the final diff.

## Approval questions

None. The user approved the complete implementation plan on 2026-09-24.

## Approved implementation plan

Implement the task intake, planning, validation, advisory model evaluation, independent review, and human handoff boundaries described in the approved Agentic Programming Pipeline for Orbit. Use one implementation agent and do not commit, push, open a PR, or merge.

## Final handoff notes

Changed behavior:

- Added the versioned local task, review, validation, evaluation, and handoff workflow.
- Backend database selection now honors `ORBIT_DATABASE_URL`; tests refuse database names that do not end in `_test`.
- Local Ollama calls now use a fixed timeout, testable clock, prompt version, and safe malformed-response handling.

Validation:

- Mandatory `All` scope passed: 12 backend tests, desktop lint/build from a locked temporary install, and `cargo check --locked`.
- The optional live `gemma3` evaluation ran and recorded a report, but 3 of 6 cases failed because the model inferred fields or omitted expressed facts.
- Bug review reported three findings and security review reported three findings. All were resolved before the final `All` gate.

Remaining risks:

- Live-model intent quality needs prompt/model hardening before the advisory evaluation can become mandatory.
- The workflow has not yet completed its three-task backend/desktop/cross-layer pilot.
- Cargo reports non-blocking hard-link fallback warnings on the repository filesystem.
- The current process-global agent state is suitable only for the explicitly
  accepted single-user, single-conversation prototype. Session isolation is
  required before concurrent or multi-user use.

Diff status:

- Branch: `main`.
- Worktree: uncommitted implementation changes; no unrelated tracked changes were introduced.
- Commit, push, pull request, and merge: not performed by the agent.
