# Data Model: Analyze a Call

**Primary use case**: `AnalyzeCall`

**No schema change**: the feature reads `calls`, `procedures` and `call_turns`. It writes nothing.

## Domain (`backend/app/domain/call_analysis.py`, standard library only)

| Item | Shape / rule |
| --- | --- |
| `CallToAnalyze` | `id: int`, `external_id: str`, `call_type: str`, `metadata: dict`, `raw_transcript: list[dict]`, `rules: dict` |
| `PromptPreview` | `id`, `external_id`, `call_type`, `prompt` |
| `ModelAnalysis` | `id`, `external_id`, `call_type`, `model`, `result: Any \| None`, `raw: str` |
| `CallNotFound(call_id)` | `str()` = `no call with id <id>` |
| `NoTranscript(call_id)` | `str()` = `call <id> has no transcript stored` |
| `transcript_from_turns(turns)` | `[(speaker, text), …]` → `[{"index": i, "speaker_role": speaker, "human_transcript": text}]`, numbered `i` from 1 |
| `agent_name_from_metadata(metadata)` | `metadata.agent.metadata.agent_name`, or `None` |
| `build_prompt(common, proc, transcript, agent_name)` | Verbatim from the old module. Steps are listed only if they have no sub-checks, or have a `confirmation_evidence` sub-check. Turns use `index` or their position, and the human text or else the machine text. The agent name defaults to `"unknown"`. |
| `clean_answer(text)` | Removes `<think>.*?</think>` (DOTALL), then strips |
| `parse_answer(cleaned)` | `json.loads`, or `None` on `ValueError` |

## Application (`backend/app/application/ports.py`, `analyze_call.py`)

| Item | Shape |
| --- | --- |
| `CallAnalysisSource` | `async load(call_id) -> CallToAnalyze \| None`; `async turns(call_id) -> list[tuple[str, str]]` |
| `PromptTemplateSource` | `async load() -> dict`. Raises `RulesUnavailable` |
| `LanguageModel` | `async ask(prompt, model) -> (model_name, text)`. Raises `ModelUnavailable` |
| `RulesUnavailable(path)` | `str()` = `missing rules file: <path> (set RULES_DIR)` |
| `ModelUnavailable(reason)` | `str()` = `could not get an answer from Ollama: <reason>` |
| `AnalyzeCall` | `calls`, `template`, `model`. `async execute(call_id, model_name=None, dry_run=False) -> PromptPreview \| ModelAnalysis`. Order: call (404) → transcript (422) → template (503) → prompt → dry run or model (503). |

## Response mapping (`backend/app/adapters/http/analyze.py`)

| Case | Status | Body |
| --- | --- | --- |
| Dry run | 200 | `{"id", "external_id", "call_type", "prompt"}` |
| Analysis | 200 | `{"id", "external_id", "call_type", "model", "result", "raw"}` |
| `CallNotFound` | 404 | `{"detail": "no call with id <id>"}` |
| `NoTranscript` | 422 | `{"detail": "call <id> has no transcript stored"}` |
| `RulesUnavailable` / `ModelUnavailable` | 503 | `{"detail": "<message>"}` |
