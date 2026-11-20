# Data Model: Demo Step Evidence

All types are frozen dataclasses in `app/domain/demo_results.py` (standard library only) unless another module is named. Changes are relative to feature 002's [data model](../002-apply-demo-results/data-model.md).

## Types

### `ResultsRow` (extended)

| Field | Type | Notes |
| --- | --- | --- |
| …existing fields… | | `demo_id`, `external_id`, `call_type`, `date`, `time`, `missed`, `wrong` |
| `evidence_step` | `str = ""` | raw, stripped |
| `evidence_turn` | `str = ""` | raw, stripped; parsed by the domain |
| `evidence_quote` | `str = ""` | raw, stripped |

### `StepEvidence` (new)

| Field | Type |
| --- | --- |
| `step` | `str` (step key) |
| `turn` | `int` (≥ 1, a stored turn index of the call) |
| `quote` | `str` (non-empty) |

### `ScoredStep` (extended)

| Field | Type | Notes |
| --- | --- | --- |
| …existing fields… | | `key`, `status`, `severity`, `points_lost`, `detail` |
| `evidence_turn` | `int \| None = None` | set only on the step named by the row's evidence |
| `evidence_quote` | `str \| None = None` | same |

## Functions

| Function | Signature | Rule |
| --- | --- | --- |
| `has_evidence` | `(row) -> bool` | Any of the three evidence values is non-empty. |
| `evidence_problems` | `(row, turns: Mapping[int, str]) -> list[str]` | Returns `[]` when there is no evidence. Otherwise it returns, in order and each prefixed `"<demo_id>: "`: partial → `evidence needs evidence_step, evidence_turn and evidence_quote` (and stops). Turn not a whole number ≥ 1 → `bad evidence turn <value>` (and stops). Step not in `row.missed \| row.wrong` → `evidence step <key> is not missed or wrong`. Turn not in `turns` → `call has no turn <n>`. Otherwise, quote not a substring of `turns[n]` → `quote not in turn <n>`. |
| `evidence_for` | `(row) -> StepEvidence \| None` | `None` when there is no evidence. Otherwise it parses the turn. Call it only after `evidence_problems` returned `[]`. |
| `score_call` (changed) | unchanged signature | Each `ScoredStep` whose key equals `evidence_for(row).step` gets `evidence_turn` and `evidence_quote`. All other steps get `None`. Status, severity, points and totals are unchanged. |

## Port: `DemoCallStore` (in `app/application/ports.py`)

| Method | Change |
| --- | --- |
| `find_calls` | unchanged |
| `find_turns(external_ids: Collection[str]) -> Mapping[str, Mapping[int, str]]` | **new**: each listed call's turns as `idx → text`. A call with no turns, or no such call, is absent. |
| `save_results` | unchanged signature. It now also writes each step's evidence fields. |

## Use case: `ApplyDemoResults.execute` (changed)

1. `stored = find_calls(ids)` (unchanged).
2. `evidence_ids` = the de-duplicated external ids of rows where `has_evidence(row)` and the call is in `stored`.
3. `turns = await store.find_turns(evidence_ids)` when `evidence_ids` is non-empty, otherwise `{}`.
4. `problems` = the duplicate problems, then for each row its `row_problems`, plus `evidence_problems(row, turns.get(id, {}))` when the call is loaded.
5. Unchanged: if there are problems, nothing is saved; otherwise `save_results([score_call(...)])`.

## Adapter: `demo_call_store.py`

| Item | Definition |
| --- | --- |
| `FIND_TURNS` | `SELECT calls.external_id, call_turns.idx, call_turns.text FROM calls JOIN call_turns ON call_turns.call_id = calls.id WHERE calls.external_id IN :external_ids ORDER BY external_id, idx` |
| `to_turn_texts(rows)` | groups the rows into `{external_id: {idx: text}}` |
| `find_turns` | returns `{}` for an empty id list without querying; otherwise runs `FIND_TURNS` and calls `to_turn_texts` |
| `UPDATE_STEP` | also sets `evidence_turn_idx = :b_evidence_turn_idx` and `evidence_quote = :b_evidence_quote` |
| `step_params` | adds `b_evidence_turn_idx` and `b_evidence_quote` |

## Adapter: `demo_results_files.py`

`read_results_csv` reads `evidence_step`, `evidence_turn` and `evidence_quote` with `(r.get(col) or "").strip()`. A missing column or a short row gives `""`. The required columns are unchanged.

## Stored state after apply (demo_48)

| Call | Step | evidence_turn_idx | evidence_quote |
| --- | --- | --- | --- |
| `a2f086d27b3a4f96` | `submit_and_confirm_transfer` | 9 | `okay and that was from your savings to your checking account` |
| every other step of every applied call | | NULL | NULL |
