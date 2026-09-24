# Roadmap

The roadmap below is based on the current project roadmap exported from Notion.

| Milestone | Status | Period | Priority |
|---|---|---|---|
| Product Definition | Done | September 2026 | |
| Core Agent | In progress | Sep–Oct | |
| Memory | Not started | Oct onward | |
| Total integrations | Not started | Nov–Dec | |
| Planning | Not started | Jan–Feb | |
| Agent Intelligence | Not started | Feb–Mar | |
| Reliability | Not started | Mar–Apr | |
| User Testing | Not started | Apr–Jun | |
| MVP | Not started | Jun–Aug | |

## Current milestone: Core Agent

The current backlog export contains:

- **Design Domain Model**
  - Type: Infrastructure
  - Status: Done
  - Priority: P2

The initial domain model, stateful proposal flow, desktop review experience,
local agentic development workflow, and persistent session-scoped draft
conversations are implemented. Conversation UUIDs isolate local state and
support restart recovery, but do not yet provide a multi-user security
boundary.

## Product progression

```text
Product Definition
       ↓
Core Agent
       ↓
Memory
       ↓
Integrations
       ↓
Planning
       ↓
Agent Intelligence
       ↓
Reliability
       ↓
User Testing
       ↓
MVP
```

## Long-term product stages

The product definition describes the user-facing progression as:

```text
MVP
 ↓
Remember & Remind
 ↓
Plan My Day
 ↓
Plan My Week
 ↓
Manage My Goals
```

These two views serve different purposes:

- The **engineering roadmap** tracks development milestones.
- The **product stages** describe increasing capability.

They should not be treated as identical timelines.

## Roadmap principles

- Prove the core interaction before adding broad capabilities.
- Do not pull future features into the MVP without a validated reason.
- Use real personal usage to determine what should be built next.
- Update this document when roadmap priorities materially change.
