# Decisions

This file records decisions that should remain understandable even after the original discussion is forgotten.

## D001 — Personal-first MVP

**Decision:** Build the MVP primarily for personal use.

**Reason:** The product hypothesis should be validated through real usage before adding multi-user complexity.

**Consequence:** Avoid authentication, tenancy, billing, and other SaaS infrastructure unless they become necessary.

## D002 — Chat-first interface

**Decision:** The MVP is primarily chat-based.

**Reason:** The central interaction is expressing an intention naturally rather than manually filling a productivity form.

**Consequence:** Fast input, clear proposals, approval, modification, rejection, and progress reporting take priority over a sophisticated dashboard.

## D003 — Orbit database is the source of truth

**Decision:** Orbit owns its internal domain state.

**Reason:** External productivity services should be integrations rather than defining Orbit's internal model.

**Consequence:** Google Calendar and Google Tasks are execution/productivity surfaces connected through adapters.

## D004 — Google Calendar and Google Tasks are initial integrations

**Decision:** Start with Google Calendar and Google Tasks.

**Reason:** They cover calendar availability/execution and task management while keeping the initial integration scope manageable.

**Consequence:** Integration interfaces should be designed so additional providers can be added later.

## D005 — Ask rather than assume

**Decision:** Orbit asks for important unknown information.

**Reason:** Inventing deadlines, durations, priorities, goals, or constraints can create incorrect or harmful plans.

**Consequence:** Unknown important fields are first-class states in the agent workflow.

## D006 — User approves important actions

**Decision:** Orbit uses risk/priority-based autonomy.

**Reason:** The AI should reduce effort without taking inappropriate consequential actions.

**Consequence:** Important calendar changes and ambiguous/high-priority decisions require explicit approval.

## D007 — Manual progress reporting initially

**Decision:** The user reports progress during the MVP.

**Reason:** Automatic verification adds significant integration and reliability complexity before the core planning loop is proven.

**Consequence:** The system must not treat a scheduled event as evidence that work was completed.

## D008 — Simple MVP task model

**Decision:** Avoid a complex Goal → Activity → Task hierarchy in the MVP.

**Reason:** The first product stage is about reliably turning intentions into actions. Premature domain complexity could slow validation.

**Consequence:** Keep the task representation small and extensible.

## D009 — Gradual autonomy

**Decision:** Autonomy should increase only as reliability and user trust increase.

**Reason:** Full autonomy is a long-term goal, not an MVP requirement.

**Consequence:** The system begins with propose/approve/execute flows and can later move toward more autonomous behaviour.

## D010 — Separate planning from execution

**Decision:** AI reasoning should be separated from external tool execution.

**Reason:** An AI can propose an action without necessarily having permission to perform it.

**Consequence:** Controlled tools/integration adapters form an execution boundary.

## D011 — Initial principle: when in doubt, ask

**Decision:** Ambiguous important decisions should trigger clarification.

**Reason:** User control is more important than pretending to know.

**Consequence:** Optimising away all clarification questions is not a product goal.

## D012 — In-memory draft conversations for the initial feedback loop

**Decision:** Keep the active task draft and its confirmation state in the
agent process for the first implementation.

**Reason:** It proves the multi-turn capture and approval flow without adding
persistence or a new domain table before recovery requirements are validated.

**Consequence:** A restart loses an unfinished draft; a persisted conversation
model can replace this boundary later.

## D013 — Persist drafts by client-held conversation UUID

**Decision:** Store each active task draft in PostgreSQL and address it with a
UUID retained by the desktop client. Persist the draft and lifecycle state, but
not the chat transcript.

**Reason:** Drafts must survive restarts and must not share process-global
state. A UUID is the smallest mechanism that supports restoration and isolated
local conversations without introducing user accounts prematurely.

**Consequence:** Approval operates on the server-stored draft and can be made
idempotent. The UUID is state correlation, not authentication; Orbit remains
single-user until an explicit identity and authorization model is introduced.

## D014 — Validate model extraction against user evidence

**Decision:** Treat local-model output as untrusted candidate data. Require
source evidence for extracted task fields and pass it through deterministic
validation before merging it into a draft.

**Reason:** Prompt instructions alone cannot reliably prevent a model from
inventing a deadline, priority, or other important fact. Orbit's
ask-rather-than-assume principle requires an enforcement boundary outside the
model.

**Consequence:** Evidence metadata stays outside the task domain, supported
date and time expressions are resolved deterministically, and ambiguity or
multiple tasks produce clarification rather than silent selection. Production
and advisory evaluation share the same extraction and validation path.
