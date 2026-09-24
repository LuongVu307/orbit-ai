---
schema_version: 1
task_id: ORBIT-0002
title: Persist and isolate draft conversations
status: completed
---

## Objective

Persist task drafts in PostgreSQL and address them by a client-held UUID so an
unfinished conversation survives restarts and cannot be confused with another
conversation.

## Motivation

The current process-global draft is lost on restart and shared by every caller.
Orbit needs durable state before it can safely grow beyond the first local
single-conversation prototype.

## Acceptance criteria

- Drafts survive backend and desktop restarts.
- Each conversation has a UUID and can affect only its own draft.
- Approval uses the server-stored draft and creates at most one task.
- Cancellation creates no task.
- Unknown conversation IDs return `404`.
- The desktop restores an unfinished draft and clears terminal conversations.
- Full chat-history persistence and authentication are not introduced.

## Non-goals

- Multi-user authentication or authorization.
- Persisting chat transcripts.
- Calendar or Google Tasks integration.
- Multiple simultaneous drafts in the desktop interface.

## Constraints and relevant decisions

- Orbit remains a personal, single-user MVP.
- A conversation UUID correlates state but is not an authentication boundary.
- The Orbit database remains the source of truth.
- Task execution remains behind explicit approval.

## Affected product behaviour

Unfinished task drafts can be restored after a restart. Approval and
cancellation operate on a specific persisted conversation rather than global
process memory.

## Validation requirements

- Test persistence, isolation, restoration, cancellation, and idempotent
  approval against the isolated PostgreSQL test database.
- Run the mandatory `All` validation scope.
- Run fresh bug and security reviews over the final diff.

## Approval questions

None. The user approved the scoped plan on 2026-09-24.

## Approved implementation plan

Add a persisted conversation model and service, make the agent stateless,
extend the API with conversation IDs and restoration, and store the active UUID
in the desktop client. Do not add authentication or chat-history persistence.

## Final handoff notes

Changed behavior:

- Draft conversations are stored in PostgreSQL and addressed by UUID.
- The agent no longer owns process-global mutable conversation state.
- Approval uses the stored draft, takes a row lock, and creates at most one
  task before marking the conversation executed in the same transaction.
- The desktop retains and restores its active conversation UUID.

Validation:

- Mandatory `All` scope passed: 13 backend tests, desktop lint/build, and
  `cargo check --locked`.
- Bugbot found one duplicate-restoration issue caused by React Strict Mode; an
  idempotence guard was added before the final validation pass.
- Security Review found no issues under the documented single-user, local-use
  threat model.

Remaining risks:

- Conversation UUIDs are bearer identifiers, not authentication credentials.
  Authentication and authorization are required before multi-user or
  network-exposed deployment.
- Chat transcripts are not persisted by design.
