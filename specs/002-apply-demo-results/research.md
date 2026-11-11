# Research: Apply Demo Results

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Primary use case**: `ApplyDemoResults`

No Technical Context item was left as NEEDS CLARIFICATION. Each decision below settles a design choice the spec leaves open.

## R1. Where the severity band rule lives (no second band table)

- **Decision**: The domain function `severity_for(bands, points_lost)` takes the bands as data. The outer edge reads that data from `docs/procedures/schema3/_common.json` → `severity.bands`, the same file `call_parse._band` reads. A unit test checks that `severity_for` gives the same answer as `call_parse._band` for every points-lost value from 0 to 100 against the real `_common.json`, so the two cannot drift apart.
- **Rationale**:
  - The band table stays in one place, the shared procedure rules, and nothing is hardcoded.
  - Importing `call_parse._band` from the domain would make the domain depend on a module outside the domain layer, and on a private name.
  - Moving `_band` into the domain and editing `call_parse.py` to use it would touch `call_parse.py`. The governance rule would then require bringing that whole file into compliance, including the seed scoring in `seed_steps`. That is a second use case and outside this slice.
- **Alternatives considered**:
  - The rejected script's hardcoded `band()`: rejected, because it is a second band table.
  - Importing `app.call_parse._band` into the domain: rejected, because of the dependency direction and the private name.
  - Refactoring `call_parse.py` to delegate: deferred to a later feature, with the reason recorded in plan.md under Out of scope.

## R2. Toronto local time

- **Decision**: `toronto_start(date, time)` combines `YYYY-MM-DD` and `HH:MM` with the standard library's `zoneinfo.ZoneInfo("America/Toronto")` and returns an aware UTC datetime. A malformed date or time raises `ValueError`. The use case turns that into a reported problem for the row.
- **Rationale**:
  - zoneinfo is standard library, so no new dependency is needed (Principle V).
  - It handles daylight saving per date: 2026-10-07 16:48 → 20:48 UTC.
  - It ships with the uv-managed Python on the host, which is the run path in the brief.
- **Alternatives considered**:
  - A fixed −04:00 offset: wrong for dates in winter time.
  - `pytz`: a new dependency.
- **Note**: if `python:3.12-slim` lacks system tz data, running the command inside the container fails loudly with `ZoneInfoNotFoundError` rather than storing wrong times. The documented run path is the host, so no `tzdata` package is added.

## R3. All-or-nothing

- **Decision**:
  - The use case validates every row before it calls the save port, using two pure domain checks:
    - `duplicate_problems(rows)`, across rows;
    - `row_problems(row, stored)`, for each row.

    If any row has a problem, it returns `saved=False` with all problems and never calls save.
  - **The outer command owns the unit of work.** It runs the whole use case inside one `async with session.begin():` block, which commits on success and rolls back on any exception.
  - The adapter's `save_results` only issues the updates and never begins or commits a transaction itself.
  - A CSV that cannot be parsed fails before the use case runs, so nothing is saved.
- **Rationale**:
  - FR-008 and FR-009 need all problems reported and nothing saved. Validating first keeps that rule in the application and domain layers.
  - **Why the command owns the transaction**: SQLAlchemy 2's `AsyncSession` starts a transaction automatically on its first query. `find_calls` reads before `save_results` writes, so a `session.begin()` inside `save_results` would raise "a transaction is already begun". A single outer `begin()` around both the reads and the writes is the standard unit-of-work pattern and avoids this.
  - The transaction also covers failures the validation cannot foresee, such as a database error mid-save.
- **Testing**: a small helper in the command module, `apply_with_session(session, rows, bands)`, does the session wiring. It is tested with a fake session that records `begin()` entry and exit, including exit with an exception.
- **Alternative considered**: the rejected script's pattern of update, then roll back if problems: it mixes validation into the SQL loop and makes the rule depend on the driver.

## R4. Persistence access

- **Decision**:
  - `SqlAlchemyDemoCallStore` in `backend/app/adapters/persistence/demo_call_store.py` uses the async SQLAlchemy session from `engine.py` and the existing mapped `Call` and `CallStep` classes in `app.models` (imported, not edited).
  - `find_calls(external_ids)` loads each call's `call_type` and its steps (key, name, points, status, detail).
  - `save_results(scored)` updates `calls` and `call_steps` inside the caller's transaction (R3).
- **Rationale**:
  - Principle III requires async SQLAlchemy, not psycopg.
  - The repo's adapter pattern is `SqlAlchemyDatabaseProbe`.
  - Reusing the mapped classes avoids a second mapping of the same tables. No schema change, so no migration.
- **Testing**: the backend suite runs without a database (see `test_engine.py`). Adapter methods are tested with a recording fake `AsyncSession`, which checks:
  - that the expected statements and parameters are issued;
  - that every update targets only the listed calls (FR-010);
  - that `save_results` does not call `begin()` or `commit()` itself. The real database is exercised by [quickstart.md](quickstart.md).
- **Alternatives considered**:
  - Raw psycopg like `load_calls.py`: rejected, because it is synchronous.
  - A live-database pytest: rejected, because the suite is database-free today and adding it would change the test setup for every teammate.

## R5. Reading the CSV and the bands

- **Decision**: `backend/app/adapters/files/demo_results_files.py` has two functions:
  - `read_results_csv(path) -> list[ResultsRow]`: `csv.DictReader`. Missing required columns raise `ValueError` naming them.
  - `read_severity_bands(rules_dir) -> tuple[SeverityBand, ...]`: reads `_common.json`.

  These are file adapters. The use case receives domain objects, not paths.
- **Rationale**: file formats belong at the adapter layer, which keeps the use case testable with in-memory rows.
- **Alternative considered**: a `ResultsSource` port. Rejected: it adds a second port for a one-shot read the command can do before calling the use case. The single persistence port is enough for "update the matching calls through a port".

## R6. Outer command

- **Decision**:
  - `backend/app/infrastructure/apply_demo_results.py` has `main(argv=None) -> int`. It parses `results_csv` and `--rules-dir`, reads the files through the R5 adapters, opens an async session, and runs `apply_with_session(session, rows, bands)` with `asyncio.run`. That helper builds the store and runs the use case inside one `session.begin()` (R3). The command then prints a summary, and returns 0 when saved and 1 otherwise.
  - pyproject gets a script entry `apply-demo-results = "app.infrastructure.apply_demo_results:main"`.
  - The module also runs with `python -m app.infrastructure.apply_demo_results`.
- **Rationale**: it matches the existing `uv run serve/migrate/test` entry points in `app.infrastructure.commands`. The edge only wires and reports.
- **Run path**: `uv run apply-demo-results ../sample/demo_48/results.csv` after `uv run python -m app.load_calls ../sample/demo_48 --demo-results`.
- **Alternative considered**: adding to `commands.py`. Rejected: those are process launchers with a `ProcessRunner` seam, while this command runs a use case in process. A separate module keeps `commands.py` unchanged.

## R7. Step note (detail) and other fields

- **Decision**: a step's `detail` is kept when its status is unchanged and set to null otherwise, as the spec's edge case says.
  - `points_under_review` is set to 0, and the call's `steps_under_review` to 0.
  - Call `status` becomes `scored`.
  - `sub_checks`, `comparison`, the evidence fields and `coaching` are not touched.
- **Rationale**: this is the rejected script's observable behavior, and the spec keeps it.

## R8. The rejected file

- **Decision**: `backend/app/apply_results.py` does not exist on `origin/feat/get_calls`, the base of this branch, and this feature does not add it. A task checks that it is absent and that no module imports `psycopg` directly for this feature. The DEMO_TODAY edit in `calls_api.py` is likewise absent and belongs to feature ListCalls.
