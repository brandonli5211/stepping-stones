<!--
Sync Impact Report
- Version change: 1.3.0 → 1.4.0
- Rationale: workflow guidance expanded for compact Speckit plans/tasks.
- Modified principles: none renamed; Principle VII unchanged in meaning
- Added sections: none
- Workflow update: each feature plans/tasks one Clean Architecture use
  case; plan Summary must name it; tasks.md limited to about 5–6 tasks
- Follow-up TODOs: none
-->

# Stepping Stones Constitution

## Core Principles

### I. Server Owns the Judgment

The frontend MUST display coaching results. It MUST NOT decide whether a
required step was completed, and it MUST NOT compute the score. Those
judgments MUST live in the Python backend, which is the single source of
the rubric.

Rationale: customer scores and polite wording do not show whether the
agent followed the template. The screen shows the check. The API makes it.

### II. Asynchronous API

The API MUST be Python and FastAPI. Every route handler MUST be declared
with `async def`. Synchronous route handlers are forbidden, including
health and utility endpoints.

Rationale: the request path stays non-blocking so database and other I/O
can proceed without tying up a worker for the life of the call.

### III. Asynchronous Persistence

PostgreSQL 18 is the only application database. Other database products
and other PostgreSQL major versions MUST NOT be used, locally or in the
running environment.

Application code MUST access it through SQLAlchemy's async engine and
async sessions. Synchronous engines, sessions, and drivers MUST NOT be
used on the request path.

Every schema change MUST ship as an Alembic migration in the same pull
request as the model change it supports. A hand-edited database is not a
source of truth.

Rationale: one major version keeps every teammate and the running
environment on the same database behavior. Async access keeps the request
path non-blocking.

### IV. Typed Component UI

The frontend MUST be React with TypeScript. Styling MUST use Tailwind CSS.
Shared interface components MUST come from shadcn/ui. New frontend source
MUST be `.ts` or `.tsx`. New `.js` or `.jsx` files are forbidden.

### V. One Stack

A new language, framework, database, ORM, migration tool, package manager,
or component library MUST NOT be introduced without an amendment to this
constitution. Local development MUST keep running the frontend, the API,
and PostgreSQL 18 together through Docker Compose.

Python dependencies MUST be managed with uv. uv is the only tool that may
install, lock, or update those dependencies. The frontend's JavaScript
dependencies MUST be managed with npm. uv MUST NOT replace npm for the
frontend.

Rationale: one Python lock shared by developers and the running
application stops two install paths from drifting apart.

### VI. Unit Test Every New Function

Every new function, in the frontend and in the backend, MUST ship with a
unit test in the same pull request. The test MUST call that function and
assert its result or the failure it is specified to raise. A new function
without a unit test MUST NOT be merged.

When an existing function's behavior changes, its unit test MUST be added
or updated in the same pull request.

Rationale: an untested function can change without a failing check. The
test is part of the change, not a follow-up.

### VII. Clean Architecture (NON-NEGOTIABLE)

Every feature that is specified, planned, tasked, or implemented MUST use
Clean Architecture. Source MUST be organized so dependencies point inward:
frameworks and drivers depend on interface adapters; adapters depend on
application use cases; use cases depend on domain entities. Inner layers
MUST NOT import outer layers.

For the backend, that means at minimum:

- Domain entities and pure domain rules MUST NOT import FastAPI,
  SQLAlchemy, Alembic, HTTP clients, or UI code.
- Application use cases MUST express the feature's behavior. They MUST
  depend on domain types and on ports (interfaces) for persistence and
  external services. They MUST NOT import FastAPI route modules or
  concrete SQLAlchemy session wiring.
- Interface adapters (repositories, presenters, DTO mappers) MAY depend
  on the application and domain layers. They MUST adapt between those
  layers and infrastructure.
- FastAPI routers, SQLAlchemy models/engines, and other frameworks MUST
  live at the outer edge. Route handlers MUST delegate to use cases; they
  MUST NOT embed scoring, step-checking, or other domain logic.

For the frontend, that means at minimum:

- UI components MUST render state and dispatch user intent. They MUST NOT
  embed domain judgment reserved for the backend (see Principle I).
- API access, DTO mapping, and view-model shaping MUST sit outside presentational
  components so screens depend on application-facing modules, not on raw
  transport details scattered through JSX.

A feature plan, task list, or pull request that places business rules in
routers, database models, or React components, or that lets domain/use-case
code import FastAPI or SQLAlchemy, MUST NOT be accepted.

Rationale: coaching judgment and feature behavior must stay testable and
replaceable without rewriting the framework shell. Clean Architecture keeps
the rubric and use cases independent of FastAPI, Postgres wiring, and React.

## Technology Constraints

- Frontend: React, TypeScript, Tailwind CSS, and shadcn/ui, built with Vite.
  JavaScript dependencies MUST be installed with npm. The agent screen
  stays a client of the API.
- Backend: Python and FastAPI. Python dependencies MUST be declared,
  locked, and installed with uv. `/docs` remains the catalog of every
  endpoint. Step checking and scoring stay in this service.
- Data: PostgreSQL 18, async SQLAlchemy, and Alembic. The frontend MUST
  NOT open a database connection.
- A transcript MAY be stored as JSON in PostgreSQL. Progress questions
  MUST remain SQL filters: this agent, this task type, this step.
- Feature modules MUST follow Clean Architecture layering (Principle VII).

## Development Workflow

- Branch names MUST match `type/issue-number-short-name`. Allowed types
  are `feat`, `fix`, `docs`, and `chore`.
- A pull request MUST cover one issue. When it finishes that issue, the
  description MUST include `Closes #<issue number>`. A page change MUST
  include a screenshot beside its Figma frame.
- At least one teammate MUST approve a pull request before it merges. The
  author MUST NOT merge their own pull request without that review.
- Reviewers MUST reject a change that adds a synchronous FastAPI handler,
  a synchronous SQLAlchemy session on the request path, a schema change
  without an Alembic migration, a database other than PostgreSQL 18, a
  Python dependency install that bypasses uv, frontend code outside
  TypeScript, Tailwind CSS, and shadcn/ui, a new or changed function
  without a unit test, or feature code that violates Clean Architecture
  (domain or use-case code importing FastAPI/SQLAlchemy, business rules in
  routers or React components, or missing use-case / port boundaries).
- Spec Kit plans and tasks for a feature MUST name the Clean Architecture
  layers the work will touch and MUST NOT schedule domain logic inside
  framework or UI modules.
- Each feature's `plan.md` Summary MUST name exactly one primary
  application use case and summarize the inward dependency path for that
  use case. Additional use cases belong in a later feature, not in the
  same plan.
- Each feature's `tasks.md` MUST implement that one use case as a single
  vertical slice. The task list MUST stay around 5–6 tasks and MUST NOT
  exceed 6. Stakeholder stories in `spec.md` MAY inform the use case; they
  MUST NOT explode into separate multi-phase story task trees.
- A ticket moves Backlog → Ready → In progress → In review → Done. Move it
  to In progress when work starts, to In review when the pull request
  opens, and to Done when it merges.

## Governance

This constitution supersedes conflicting practice, including starter code
that still uses synchronous SQLAlchemy, JavaScript, PostgreSQL 16, or an
unlocked pip install. New and changed code MUST comply. A change that
touches a non-compliant file MUST bring that file into compliance in the
same change.

An amendment MUST be a pull request that updates this file, states the
version bump, and receives one teammate's approval before merge.

Versioning follows semantic versioning:

- MAJOR: a principle is removed or redefined so that existing guidance no
  longer holds.
- MINOR: a principle or section is added, or guidance is materially
  expanded.
- PATCH: wording is clarified and the rule itself does not change.

**Version**: 1.4.0 | **Ratified**: 2026-10-27 | **Last Amended**: 2026-11-08
