---

description: "Task list for Demo Step Evidence (ApplyDemoResults extended, issue #33)"
---

# Tasks: Demo Step Evidence

**Input**: Design documents from `/specs/005-demo-step-evidence/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/apply-demo-results-command.md, quickstart.md, constitution.md (1.5.0)

**Tests**: cut on 2026-11-19 at the product owner's request. This does not meet constitution VI; the deviation is recorded in plan.md Complexity Tracking. The tests need no database. The real database is checked in T005 through quickstart.md.

**Organization**: ONE Clean Architecture use case, `ApplyDemoResults` extended (plan.md Summary), as a single vertical slice of 5 tasks. Spec stories US1 (evidence is stored) and US2 (unverifiable evidence saves nothing) are both served by this one slice.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: `[US1]` = the single use-case slice
- Paths are relative to the repository root

## Use Case: ApplyDemoResults, extended (from plan.md Summary)

**Goal**: applying `sample/demo_48/results.csv` stores evidence turn 9 and the quote "okay and that was from your savings to your checking account" on step `submit_and_confirm_transfer` of call `a2f086d27b3a4f96`. Evidence that cannot be verified saves nothing. Nothing else changes.

**Independent Test** (full commands in quickstart.md):
1. `uv run test` is green.
2. After load and apply, exactly one step has evidence: the one above, with turn start 33.53 s. Its status, severity, points lost, call score and comparison are unchanged (wrong, critical, 55, 45, three rows).
3. A copy of the file with one word of the quote changed exits 1, reports `HVB-DEMO-06: quote not in turn 9`, and changes nothing.

- [X] T001 [US1] **Domain.** Edit `backend/app/domain/demo_results.py` (standard library only).
  - **`ResultsRow`**: add `evidence_step: str = ""`, `evidence_turn: str = ""`, `evidence_quote: str = ""` after the existing fields, so existing constructor calls stay valid.
  - **New `StepEvidence(step: str, turn: int, quote: str)`**: frozen dataclass.
  - **`ScoredStep`**: add `evidence_turn: int | None = None` and `evidence_quote: str | None = None`.
  - **`has_evidence(row)`**: "Any of the three evidence values is non-empty."
  - **`evidence_problems(row, turns: Mapping[int, str]) -> list[str]`**: returns `[]` without evidence. Otherwise problems prefixed `"<demo_id>: "`, in order:
    1. not all three filled → `evidence needs evidence_step, evidence_turn and evidence_quote`, and return;
    2. turn not a whole number ≥ 1 (`str.isdigit()` and `int(...) >= 1`) → `bad evidence turn <value>`, and return;
    3. step not in `row.missed | row.wrong` → `evidence step <key> is not missed or wrong`;
    4. turn not in `turns` → `call has no turn <n>`; otherwise, quote not a substring of `turns[n]` (exact, case-sensitive) → `quote not in turn <n>`.
  - **`evidence_for(row) -> StepEvidence | None`**: `None` without evidence; otherwise the parsed turn and stripped values.
  - **`score_call`**: the step whose key equals `evidence_for(row).step` gets `evidence_turn` and `evidence_quote`. All other steps get `None`. Status, severity, points, detail and totals are unchanged.
  - **Tests**: no unit test of its own (2026-11-19 test cut). The rules are covered through the evidence cases in T002 and the data test in T005.
- [X] T002 [US1] **Port and use case.** Edit `backend/app/application/ports.py`: add `find_turns(self, external_ids: Collection[str]) -> Mapping[str, Mapping[int, str]]` to `DemoCallStore`, documented as "Each listed call's stored turns as idx → text. Calls with no turns are absent." Edit `backend/app/application/apply_demo_results.py` per data-model.md:
  - `evidence_ids` = de-duplicated ids of rows where `has_evidence(row)` and the call is in `stored`;
  - `turns = await self.store.find_turns(evidence_ids)` only when non-empty, otherwise `{}`;
  - for each loaded row, add `evidence_problems(r, turns.get(r.external_id, {}))` after `row_problems`.

  Update `backend/tests/test_apply_demo_results.py`: `FakeStore.find_turns` serves stored turns, and `test_bad_file_saves_nothing` gains 5 cases, one per evidence problem (missing value, bad turn, step not missed or wrong, turn the call does not have, quote not in the turn). Each saves nothing.
- [X] T003 [P] [US1] **Files adapter.** Edit `backend/app/adapters/files/demo_results_files.py`: `read_results_csv` reads `evidence_step`, `evidence_turn` and `evidence_quote` with `(r.get(col) or "").strip()`. "A missing column or a short row gives `""`". `REQUIRED_COLUMNS` is unchanged. No unit test of its own (2026-11-19 test cut); the data test in T005 reads the real CSV through it.
- [X] T004 [P] [US1] **Persistence adapter.** Edit `backend/app/adapters/persistence/demo_call_store.py`:
  - **`FIND_TURNS`**: `_calls` joined to `CallTurn.__table__` on `call_id = id`, `external_id IN :external_ids` (expanding), ordered by external_id and idx.
  - **`to_turn_texts(rows) -> dict[str, dict[int, str]]`**.
  - **`SqlAlchemyDemoCallStore.find_turns`**: `{}` with no query for an empty list.
  - **`UPDATE_STEP`**: also sets `evidence_turn_idx=bindparam("b_evidence_turn_idx")` and `evidence_quote=bindparam("b_evidence_quote")`.
  - **`step_params`**: adds both keys.

  No unit test (2026-11-19 test cut). Checked only by the real database run in T005.
- [X] T005 [US1] **Data and verification.** Edit `sample/demo_48/results.csv`:
  - append `,evidence_step,evidence_turn,evidence_quote` to the header and `,,,` to every row;
  - `HVB-DEMO-06` instead ends `,submit_and_confirm_transfer,9,okay and that was from your savings to your checking account`;
  - keep LF line endings and no trailing newline, as the file has now.

  Add `backend/tests/test_demo_results_files.py` with `test_demo_48_evidence`: read the real `sample/demo_48/results.csv`, assert exactly one row has evidence (`HVB-DEMO-06`, `a2f086d27b3a4f96`, step `submit_and_confirm_transfer`, turn `9`), build `idx → text` from the real transcript file, and assert `evidence_problems(row, turns) == []` and that turn 9 is an agent turn starting at 0:33. Teach the in-memory store in `backend/tests/demo_48_data.py` to serve stored turns, and assert in `test_demo_48_numbers` that the evidence lands only on that step.

  Run `uv run test`. Run quickstart.md steps 2–4 against PostgreSQL 18 when Docker is available, and record the results here.

  **Results (2026-11-16)**:
  - `uv run test`: 53 passed (47 before this feature), as rebuilt on 2026-11-19.
  - **PostgreSQL run (2026-11-16, later the same day): passed.** quickstart.md steps 2–4 ran against PostgreSQL 18.6 in a throwaway database (`stepping_stones_verify_005`, dropped afterwards). The main database was not touched.
    - Step 2: load gave 48 calls; apply gave `{'updated': 48, 'problems': [], 'saved': True}`. Exactly one of 281 steps has evidence: `a2f086d27b3a4f96 | submit_and_confirm_transfer | wrong | critical | 55 | 9 | okay and that was from your savings to your checking account | 33.53 | 45`. Turn 9 is an agent turn, and the quote equals its stored text. The comparison table still has its three rows.
    - Step 3: one word of the quote changed gave `HVB-DEMO-06: quote not in turn 9`, exit 1. Turn changed to 17 gave `HVB-DEMO-06: call has no turn 17`, exit 1. After both, every call and step row was byte-identical to before.
    - Step 4: applying the pre-feature 7-column `results.csv` (the version before this feature) still works and leaves no step with evidence. Against that state, the new file changes only the two evidence fields of the one step. `GET /calls?limit=100&weeks=8` with `DEMO_TODAY=2026-10-09T23:59:59+00:00` is byte-identical for both: this week 53 of 59 (90%), week 1 64%, call `a2f086d27b3a4f96` score 45, "Wrong: Submit and confirm transfer".
    - Re-applying the new file gives a byte-identical database.
  - Earlier offline check (before Docker was available): all 48 calls were seeded with `parse_call` + `seed_steps` (what `load_calls --demo-results` stores), and the real `ApplyDemoResults` ran over the real CSV and bands with an in-memory store.
    - Output: `{'updated': 48, 'problems': [], 'saved': True}`; 48 calls, 281 steps; turns loaded only for `a2f086d27b3a4f96`.
    - Exactly one step has evidence: `submit_and_confirm_transfer`, wrong, critical, 55 lost, turn 9, the whole-turn quote, call score 45.
    - Every other field of every call and step equals a run with the evidence removed.
    - One word of the quote changed: `HVB-DEMO-06: quote not in turn 9`, nothing saved. Turn changed to 17: `HVB-DEMO-06: call has no turn 17`, nothing saved.

## Dependencies & Execution Order

1. T001 (domain) comes first. Every other task imports its types.
2. T002 depends on T001.
3. T003 and T004 depend only on T001 and can run in parallel with each other and with T002.
4. T005 depends on all of the above.

## Implementation Strategy

1. Implement T001→T005 in order. `uv run test` must be green before the next task.
2. Stop when the independent test above passes.

## Notes

- 5 tasks, one use case, within the 6-task ceiling.
- No schema change, so no migration. No new dependency. `app/infrastructure/apply_demo_results.py` is unchanged.
- Do not commit until asked.

## Phase 2: Convergence

- [X] T006 Convergence (2026-11-16) found `_evidence_values` and `_optional` with no direct test (Constitution VI). Direct tests were added, then removed in the 2026-11-19 test cut. Both are now covered only through `test_bad_file_saves_nothing` and `test_demo_48_evidence` (recorded deviation, plan.md Complexity Tracking).
