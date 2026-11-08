---

description: "Task list template for feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Include unit-test work inside the compact task list when constitution principle VI applies. Do not add a separate multi-phase test tree.

**Organization**: ONE Clean Architecture use case (from plan.md Summary). About **5–6 tasks total** (hard ceiling: **6**). Do not create one phase per stakeholder user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Use `[US1]` for the single use-case slice
- Include exact file paths in descriptions

## Path Conventions

- Backend CA layout (adjust to plan.md): `backend/app/domain/`, `backend/app/application/`, `backend/app/adapters/`, `backend/app/infrastructure/`, composition in `backend/app/main.py`
- Frontend: keep domain judgment out of components; API/DTO shaping outside presentational UI
- Paths below are samples — replace with real paths from plan.md

<!--
  ============================================================================
  IMPORTANT: SAMPLE TASKS ONLY. /speckit-tasks MUST replace these.

  Project constraints (constitution + Cursor rule):
  - Exactly one primary use case from plan.md Summary
  - 5–6 tasks total (never more than 6)
  - Collapse setup, wiring, tests, and polish into those tasks
  - Do NOT keep multi-story Phase 3/4/5 sprawl from older Speckit defaults
  ============================================================================
-->

## Use Case: [UseCaseName] (from plan.md Summary)

**Goal**: [What this one use case delivers end-to-end]

**Independent Test**: [How to verify the slice works]

- [ ] T001 [P] [US1] Domain: [entity/rules] in `backend/app/domain/[file].py`
- [ ] T002 [US1] Application: `[UseCaseName]` + ports in `backend/app/application/[file].py`
- [ ] T003 [US1] Adapters: persistence/HTTP/DTO mapping in `backend/app/adapters/[path]/`
- [ ] T004 [US1] Infrastructure / composition / route or UI wiring (outer edge only; delegates to use case)
- [ ] T005 [US1] Unit tests for every new or changed function in `backend/tests/` (and frontend tests if touched)
- [ ] T006 [US1] [Only if still needed within the 6-task ceiling] Migration, Compose, or quickstart validation

**Checkpoint**: The named use case works through Clean Architecture layers; domain/application do not import FastAPI or SQLAlchemy.

---

## Dependencies & Execution Order

1. Domain before application
2. Application (use case + ports) before adapters
3. Adapters before infrastructure / composition / UI wiring
4. Tests may be written first within a task, but do not add extra task rows past 6
5. No parallel multi-story tracks — one slice only

## Implementation Strategy

1. Implement T001→T00N in order (skip unused optional T006 if not needed)
2. Stop when the single use case passes its independent test
3. Further use cases → new feature spec/plan/tasks, not more rows here

## Notes

- Hard ceiling: 6 checkbox tasks
- Prefer combining small steps over adding phases
- Avoid: vague tasks, business logic in routers/models/components, second use case in the same list
