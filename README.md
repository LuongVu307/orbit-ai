# Orbit

> **Tell me what I want to accomplish. You figure out when and how.**

Orbit is a personal AI planning assistant that turns natural-language intentions and goals into realistic tasks, schedules, and adaptive plans.

The user describes **what they want to accomplish** and the constraints that matter. Orbit considers relevant goals, priorities, existing commitments, available time, and progress, then proposes **when and how** to do it.

> **The AI is responsible for planning; the user is responsible for deciding.**

## Project status

Orbit is currently in the **Core Agent** stage.

The first product milestone is a personal MVP focused on **Remember & Remind**: turning a natural-language intention into an appropriate action in the user's productivity system.

Current roadmap:

| Milestone | Status | Period |
|---|---|---|
| Product Definition | Done | September 2026 |
| Core Agent | In progress | Sep–Oct |
| Memory | Not started | Oct onward |
| Total integrations | Not started | Nov–Dec |
| Planning | Not started | Jan–Feb |
| Agent Intelligence | Not started | Feb–Mar |
| Reliability | Not started | Mar–Apr |
| User Testing | Not started | Apr–Jun |
| MVP | Not started | Jun–Aug |

## Vision

Orbit aims to remove the mental effort involved in:

- deciding what to do
- estimating how long activities will take
- finding available time
- prioritising competing work
- replanning when reality differs from the plan

The long-term loop is:

```text
GOAL
  ↓
PLAN
  ↓
PROPOSE
  ↓
USER APPROVES
  ↓
EXECUTE
  ↓
PROGRESS
  ↓
EVALUATE
  ↓
RE-PLAN
  └──────────────→ USER APPROVES
```

The product should evolve gradually from:

```text
Ask → Propose → Approve → Execute
```

towards:

```text
Observe → Decide → Act
```

without removing user control over important decisions.

## MVP

### MVP objective

Build the smallest usable version that can turn a natural-language intention into an appropriate action in the user's productivity system while reducing the mental effort required to organise it manually.

### Core workflow

```text
User intention
      ↓
AI understands intention
      ↓
AI gathers relevant context
      ↓
AI identifies missing information
      ↓
AI asks user when necessary
      ↓
AI proposes an action
      ↓
User approves / modifies / rejects
      ↓
AI executes the action
      ↓
User reports progress
      ↓
AI records the outcome
```

### MVP must have

- Natural-language chat interaction
- Task/intention understanding
- Explicit handling of unknown information
- Relevant user context
- Calendar integration
- Internal task representation
- Approval / modification / rejection
- Manual progress reporting
- Basic proactive suggestions
- Risk/priority-based autonomy

### MVP does not include

- Full long-term goal management
- Automatic goal decomposition
- Complex milestone generation
- Full weekly planning
- Sophisticated daily optimisation
- Continuous autonomous replanning
- Automatic progress verification
- Automatic learning of all personal preferences
- Voice interface
- Mobile application
- Multiple specialised agents
- Large-scale integrations
- Public multi-user product
- Advanced analytics
- Fully autonomous decision-making

## Architecture at a glance

The internal database is the source of truth. External productivity services are integrations/execution surfaces.

```text
                 ┌─────────────────┐
                 │   Chat Client   │
                 └────────┬────────┘
                          ↓
                 ┌─────────────────┐
                 │    AI Agent     │
                 │ Understand      │
                 │ Context         │
                 │ Plan            │
                 │ Propose         │
                 └────────┬────────┘
                          ↓
                 ┌─────────────────┐
                 │  Orbit Database │
                 │  Source of Truth│
                 └───────┬─┬───────┘
                         │ │
             ┌───────────┘ └───────────┐
             ↓                         ↓
   ┌──────────────────┐      ┌──────────────────┐
   │ Google Calendar  │      │   Google Tasks   │
   │ Execution surface│      │ Execution surface│
   └──────────────────┘      └──────────────────┘
```

Current implementation uses a Python/FastAPI backend, with React/TypeScript and Tauri forming the intended desktop application stack.

## Repository structure

```text
orbit-ai/
├── AGENTS.md
├── README.md
├── docs/
│   ├── product.md
│   ├── architecture.md
│   ├── decisions.md
│   ├── domain-model.md
│   ├── roadmap.md
│   └── development-log.md
├── apps/
│   ├── backend/
│   └── desktop/
```

## Development principles

1. **Ask rather than assume.** Important unknowns such as deadlines, priorities, duration, goals, and constraints should not be invented.
2. **User controls important decisions.** Orbit may propose actions, but significant actions require appropriate approval.
3. **Keep the core simple.** Avoid premature abstractions and unnecessary dependencies.
4. **Own the domain model.** The Orbit database is the source of truth rather than Google Calendar or Google Tasks.
5. **Separate planning from execution.** The AI decides what should happen; integrations carry out approved actions.
6. **Build incrementally.** Prove the core interaction before implementing the entire long-term vision.
7. **Measure user value.** The ultimate goal is meaningful progress with less planning effort.

## Success

The north-star concept is:

> **Goal Progress per Unit of Planning Effort**

The MVP should be judged primarily by:

- intent accuracy
- proposal usefulness
- approval rate
- execution reliability
- planning effort saved
- repeated personal usage

The MVP is successful when the user consistently prefers using Orbit over manually organising the same activities.

## Documentation

- [Product](docs/product.md)
- [Architecture](docs/architecture.md)
- [Domain Model](docs/domain-model.md)
- [Decisions](docs/decisions.md)
- [Roadmap](docs/roadmap.md)
- [Development Log](docs/development-log.md)
- [Agentic Development Workflow](docs/development-workflow.md)
