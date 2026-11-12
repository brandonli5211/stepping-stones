# Implementation Plan: Apply Demo Results

**Branch**: `feat/33-load-demo-48` (issue #33) | **Date**: 2026-11-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-apply-demo-results/spec.md`

This plan replaces the rejected `backend/app/apply_results.py` from PR #45. It keeps that script's behavior and gives it a Clean Architecture structure. The spec adds two validation rules: a row with a call_type mismatch is bad, and so is a row with a step listed as both missed and wrong.

## Summary

**Primary use case**: `ApplyDemoResults`. It applies curated results rows to loaded calls: it validates every row, then recomputes step status, severity, points lost, score and counts from the rubric, and saves all calls together or none.

A presenter runs `uv run apply-demo-results ../sample/demo_48/results.csv` after loading demo_48 with `--demo-results`. For each row, the command:
1. reads the call's start time as Toronto local time;
2. sets each step to missed, wrong or completed;
3. recomputes the call's numbers with the schema3 severity bands read from `_common.json`;
4. saves everything in one transaction, which the command owns.

Any bad row fails the run, every problem is reported, and nothing is saved.

**Inward dependency path**:

| Layer | Module | What it holds |
| --- | --- | --- |
| Domain | `app/domain/demo_results.py` | Pure types and rules. Standard library only. |
| Application | `app/application/apply_demo_results.py` | The use case. Depends on the domain and on the `DemoCallStore` port in `app/application/ports.py`. |
| Adapters | `app/adapters/persistence/demo_call_store.py` | The `DemoCallStore` port over the async SQLAlchemy session. |
| Adapters | `app/adapters/files/demo_results_files.py` | Reads the CSV and `_common.json` into domain types. |
| Infrastructure | `app/infrastructure/apply_demo_results.py` | CLI entry point: wires the adapters and the use case, and owns the transaction (one `session.begin()` around the use case). |

Nothing inner imports anything outer.

## Use Cases

*Accurate after Phase 0 (research) and after Phase 1 (design).*

| Use case | Responsibility | Module |
| --- | --- | --- |
| `ApplyDemoResults` (primary) | Validates every results row against its stored call, scores the valid rows with domain rules, and saves all calls through the `DemoCallStore` port only when no row has a problem. It never reads files, parses CLI arguments or touches SQL. | `backend/app/application/apply_demo_results.py` |

**Out of scope for this plan**:
- `ListCalls`: the demo clock, week window, percent and label in `calls_api.py`. That is feature B, in its own spec.
- Refactoring `call_parse.py` / `load_calls.py` (seed scoring, synchronous psycopg loader) into layers: a later feature. This feature imports neither, and edits neither.

## Technical Context

**Language/Version**: Python ≥ 3.12, as in `pyproject.toml`. The host runs 3.13 via uv, and the image runs 3.12.

**Primary Dependencies**: SQLAlchemy 2 async with psycopg 3 (existing), plus the standard library `csv`, `json`, `zoneinfo`, `argparse` and `asyncio`. There are no new dependencies.

**Storage**: PostgreSQL 18. The feature updates the existing `calls` and `call_steps` columns. There is no schema change and no migration.

**Testing**: pytest via `uv run test`, with no database required. Each new function has a test that calls it and asserts the result. The adapter is tested with a recording fake `AsyncSession`. The real database is checked by [quickstart.md](quickstart.md).

**Target Platform**: Developer and presenter machine. The command runs from `backend/` on the host.

**Project Type**: Web application backend. This feature adds a CLI command, with no route and no frontend.

**Performance Goals**: 48 rows applied in a few seconds. This is not a hot path.

**Constraints**:
- **Clean Architecture**: the domain and application layers do not import FastAPI, SQLAlchemy, Alembic or psycopg.
- **Async persistence**: async SQLAlchemy only.
- **All or nothing**: a bad file saves nothing.
- **No second band table**: the severity bands come only from `_common.json`.

**Scale/Scope**: one use case, about 5 new source modules, about 6 tasks.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Before research | After design |
| --- | --- | --- |
| I. Server owns the judgment | Pass. Step status and score are computed in the backend domain. | Pass. `score_call` is in `app/domain`. Nothing moves to React. |
| II. Asynchronous API | Pass. No route is added or changed. | Pass. |
| III. Asynchronous persistence | Pass. The rejected script's synchronous psycopg is replaced by async SQLAlchemy. No schema change, so no migration is needed. | Pass. `SqlAlchemyDemoCallStore` uses `AsyncSession`. The command wraps the use case in one `session.begin()` ([research.md](research.md) R3, R4). |
| IV. Typed component UI | Pass. No frontend change. | Pass. |
| V. One stack | Pass. The command is a uv script entry. There are no new packages. | Pass. zoneinfo, csv and json are standard library ([research.md](research.md) R2). |
| VI. Unit test every new function | Pass (planned). | Pass. Every function in [data-model.md](data-model.md) and every adapter and command function gets a test. A further test keeps `severity_for` in agreement with `call_parse._band`. |
| VII. Clean Architecture | Pass. One use case behind one port. Rules are in the domain, and the edge only wires. | Pass. The domain module is standard library only, and the use case imports only the domain and ports. An import-guard test covers `fastapi`, `sqlalchemy`, `alembic` and `psycopg`. |
| Workflow | Pass. Branch `feat/33-load-demo-48`, one issue (#33), `Closes #33` in the PR. One primary use case is named in the Summary and in Use Cases. | Pass. The task list is planned as one vertical slice of 6 tasks or fewer. |
| Governance: touched non-compliant files | Pass. `ports.py` and `pyproject.toml` are edited and are already compliant. `call_parse.py`, `load_calls.py`, `models.py` and `calls_api.py` are not edited. `app.models` is only imported, by the adapter. | Pass. |

No gate failed. Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/002-apply-demo-results/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── apply-demo-results-command.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks (not yet created)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── domain/
│   │   └── demo_results.py              # NEW  types + pure rules
│   ├── application/
│   │   ├── ports.py                     # EDIT add DemoCallStore protocol
│   │   └── apply_demo_results.py        # NEW  ApplyDemoResults use case + ApplyOutcome
│   ├── adapters/
│   │   ├── files/
│   │   │   ├── __init__.py              # NEW
│   │   │   └── demo_results_files.py    # NEW  read_results_csv, read_severity_bands
│   │   └── persistence/
│   │       └── demo_call_store.py       # NEW  SqlAlchemyDemoCallStore (async)
│   └── infrastructure/
│       └── apply_demo_results.py        # NEW  main(argv) -> exit code
├── pyproject.toml                       # EDIT add apply-demo-results script
└── tests/
    ├── test_domain_demo_results.py      # NEW
    ├── test_apply_demo_results.py       # NEW  use case with fake store
    ├── test_demo_results_files.py       # NEW
    ├── test_demo_call_store.py          # NEW  fake AsyncSession
    └── test_apply_demo_results_command.py  # NEW
sample/demo_48/                          # copied unchanged from feat/load-demo-48
```

**Structure Decision**: this follows the existing backend layering (`domain` / `application` / `adapters` / `infrastructure`) set up by feature 001. `backend/app/apply_results.py` is not created. It is absent on the base branch and stays absent.

## Complexity Tracking

No constitution violations require justification.

## Phase 0 and Phase 1 outputs

- **Phase 0**: [research.md](research.md), decisions R1–R8. No NEEDS CLARIFICATION remained.
- **Phase 1**:
  - [data-model.md](data-model.md)
  - [contracts/apply-demo-results-command.md](contracts/apply-demo-results-command.md)
  - [quickstart.md](quickstart.md)

**Post-design constitution check**: all gates still pass.
- The domain and use case import no framework or driver.
- The single port is the only path to persistence.
- The command is async end to end.
- The severity bands have one source.
- No business rule sits in a router, ORM model or UI.
- The Use Cases section lists exactly one primary use case after both phases.
