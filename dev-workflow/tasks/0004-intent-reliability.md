---
schema_version: 1
task_id: ORBIT-0004
title: Add evidence-aware intent reliability
status: completed
---

## Objective

Measure and improve local-model task understanding while preventing unsupported
model output from becoming trusted task facts.

## Motivation

The current agent workflow is deterministic after extraction, but the initial
live gemma3 evaluation passed only three of six cases. Prompt output currently
flows directly into TaskIntent, so invented or omitted fields are not separated
from user-provided facts.

## Acceptance criteria

- A versioned corpus contains at least 30 representative real-world messages.
- Reports include case, category, and field-level metrics.
- Prompt version 1 can be evaluated as a preserved baseline.
- Prompt version 2 returns source evidence and explicit ambiguity signals.
- Deterministic validation accepts only supported task facts.
- Invented deadlines and priorities are discarded.
- Important ambiguity produces a specific clarification.
- Multiple tasks are not silently collapsed into one.
- Deterministic tests do not require Ollama.
- Live evaluation remains advisory and records model and prompt versions.

## Non-goals

- Calendar or Google Tasks integration.
- Automatic creation of multiple tasks from one message.
- New persistent task fields or chat transcript storage.
- Authentication, multi-user support, or autonomous execution.
- Choosing a replacement model without evaluation evidence.

## Constraints and relevant decisions

- Follow the ask-rather-than-assume product principle.
- Evidence metadata belongs to the extraction boundary, not the task domain.
- The production path and evaluation path must share prompt, parsing, and
  validation code.
- Preserve prompt version 1 for fair baseline comparison.

## Affected product behaviour

Orbit will reject unsupported model fields and ask targeted questions when it
cannot safely interpret important task information. Valid task creation,
modification, approval, and persistence remain unchanged.

## Validation requirements

- Add deterministic tests for evidence validation, prohibited inference,
  ambiguity, multiple tasks, malformed output, and evaluation scoring.
- Capture prompt-v1 and prompt-v2 advisory reports against the same corpus when
  Ollama and gemma3 are available.
- Run the mandatory All validation scope.
- Perform fresh bug and security reviews over the final diff.

## Approval questions

None. The user approved the full architecture and implementation plan on
2026-09-26.

## Approved implementation plan

Create a versioned real-world corpus and scorer, preserve the legacy prompt,
add an evidence-aware extraction schema and deterministic validator, pass
validated understanding results into the existing conversation agent, improve
clarifications, compare prompt versions, and document measured limitations.

## Final handoff notes

Implementation is complete. Prompt v1 passed 8/37 advisory checks with 17
prohibited inferences; prompt v2 passed 29/37 with zero prohibited inferences.
The mandatory All validation scope passes with 44 backend tests, desktop lint
and build, and `cargo check --locked`. Final Bugbot and security reviews found
no remaining actionable issues.
