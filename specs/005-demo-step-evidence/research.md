# Research: Demo Step Evidence

Every Technical Context item was known. These decisions record the choices.

## R1. Where the hand-labelled evidence lives

- **Decision**: three optional columns in `sample/demo_48/results.csv`: `evidence_step`, `evidence_turn` and `evidence_quote`.
- **Rationale**: the evidence is part of the same curated outcome as the row's missed and wrong steps. One file keeps it next to the step it supports and inside the same all-or-nothing apply. The reader already ignores extra columns, so older files keep working.
- **Alternatives considered**:
  - A separate `evidence.csv`: needs a second argument, a second reader and joining by call.
  - Putting the evidence in the transcript JSON: that is third-party data, which we do not edit.
  - Hard-coding the evidence for one call: not data-driven, and untestable as a rule.

## R2. How the use case gets the turn text

- **Decision**: add `DemoCallStore.find_turns(external_ids) -> Mapping[str, Mapping[int, str]]`, mapping each call's external id to its turns (`idx → text`). The use case calls it once, only for loaded calls whose rows have evidence. It does not call it when no row has evidence.
- **Rationale**: the stored turns are what the call detail screen will show, and the foreign key on `evidence_turn_idx` points at them. The use case stays persistence-agnostic. Files without evidence do no extra work.
- **Alternatives considered**:
  - Extending `find_calls` to return turns for every call: loads about 1,000 rows that are not needed.
  - Reading the transcript JSON in the command: checks the file, not what is stored, and puts file reading on the use case's path.

## R3. Keep raw evidence strings on `ResultsRow`

- **Decision**: `ResultsRow` gains `evidence_step`, `evidence_turn` and `evidence_quote` as raw, stripped strings, defaulting to `""`. The domain parses and validates them.
- **Rationale**: a partial or non-numeric turn must be a row problem with the demo id (spec FR-002, FR-003), not a crash in the CSV reader. Defaults keep every existing `ResultsRow(...)` call and test valid.
- **Alternatives considered**: parsing to `int` in the reader. A bad value would then fail the whole file with no demo id.

## R4. Word-for-word match

- **Decision**: the check is `quote.strip()` is non-empty and `quote.strip() in turn_text`: exact and case-sensitive.
- **Rationale**: it follows the `unverifiable_means_review` judging rule ("word for word in the turn it names"), and it is simple and predictable for a hand-typed file.
- **Alternatives considered**:
  - Case- or space-insensitive matching: a looser rule than the one the analyzer will be held to.
  - Matching against the whole transcript: loses the turn reference.

## R5. Evidence travels on `ScoredStep`

- **Decision**: `ScoredStep` gains `evidence_turn: int | None = None` and `evidence_quote: str | None = None`. `score_call` sets them on the step named by `evidence_for(row)` and leaves every other step `None`. `UPDATE_STEP` writes both fields for every step.
- **Rationale**: the step update already rewrites each step. Writing `None` for unnamed steps gives FR-007 (stale evidence is cleared) and keeps re-applying idempotent, with no extra statement.
- **Alternatives considered**: a separate evidence `UPDATE`, which adds a statement and leaves stale evidence behind.

## R6. Evidence checks only run for loaded calls

- **Decision**: if the row's call is missing, only the existing "call not loaded" problem is reported. The partial-evidence and bad-turn checks need no stored data, but they still run only with a loaded call, to keep one clear message per cause.
- **Rationale**: avoids noisy follow-on messages such as "call has no turn 9" for a call that is not loaded.
- **Alternatives considered**: always running every check, which gives duplicate, confusing messages.

## R7. Problem messages

- **Decision**: the messages keep the existing `"<demo_id>: <problem>"` form:
  - `evidence needs evidence_step, evidence_turn and evidence_quote`
  - `bad evidence turn <value>`
  - `evidence step <key> is not missed or wrong`
  - `call has no turn <n>`
  - `quote not in turn <n>`
- **Rationale**: consistent with feature 002's contract, and each message names what to fix.
- **Alternatives considered**: none.
