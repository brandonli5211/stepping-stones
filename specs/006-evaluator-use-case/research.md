# Research: Evaluate Ordered Call Steps

## R1 — Analysis execution point

**Decision**: Implement an offline `uv run analyze` command that selects calls and invokes `EvaluateOrderedCall` once per completed call.

**Rationale**: Issue #38 requires analysis ahead of time and says no model work may occur while a user opens a page. The current UI already reads persisted `CallStep` state through list and detail use cases.

**Alternatives considered**: A live FastAPI evaluation route was rejected because it would analyze while a page/API consumer is active and would conflict with #38.

## R2 — Model responsibility

**Decision**: Use the OpenAI Decisions adapter only for typed observations: an eligible evidence turn, and for steps with recorded actions, a match/mismatch/unclear observation against the caller transcript. Python validates selected quotes and decides statuses, scores, severities, and flags.

**Rationale**: Decisions returns typed choices rather than arbitrary JSON. Supplying stored agent-turn IDs as choices lets Python retain exact, verifiable evidence rather than trusting model-authored text. The matcher never receives the dataset answer key.

**Alternatives considered**: Model-authored scores were rejected because they conflict with server-owned judgment. Local Ollama is intentionally deferred with the rest of #38.

## R3 — Procedure ordering and terminal state

**Decision**: Process one complete call sequentially in one transaction. A confident, non-contradictory decision completes the current step; low-confidence, contradictory, refused, malformed, or unverifiable evidence makes the current step under review. At end of call, every later definitively unobserved step becomes missed.

**Rationale**: This fixes #51's simultaneous missed/review state and guarantees that an ended call has no unexplained later steps.

**Alternatives considered**: Persisting a cursor for live streaming was rejected for this feature because #38 analyzes complete stored calls; it would add a migration and a second lifecycle without user value.

## R4 — Stored results

**Decision**: Adapt existing `Call` and `CallStep` columns, including evidence turn/quote, under-review points, comparison data, model, prompt version, and aggregate totals. Save all changes atomically.

**Rationale**: #50's call detail and existing list/progress consumers already read these fields. Reusing them preserves contracts.

**Alternatives considered**: A parallel evaluator-result table was rejected because it would duplicate data and force every current reader to change.

## R5 — Boundaries and package locations

**Decision**: Put ports in `application/ports.py`, Decisions code in `adapters/llm/`, persistence in `adapters/persistence/`, and command/controller plus presenter at the outer adapter edge. Use explicit input/output boundaries for this new slice.

**Rationale**: These are current repository conventions; the reference document's boundary roles are retained without copying its unrelated folder tree.

**Alternatives considered**: `app/ports/` and a top-level `adapters/openai_decisions.py` were rejected because they conflict with current main and #38.
