# Research: Analyze a Call

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

**Primary use case**: `AnalyzeCall`

No Technical Context item was left as NEEDS CLARIFICATION. The user decided three things beforehand:
- verification uses the dry run and a stand-in model;
- `calls_api.py` is deleted;
- `load_calls.py` and `call_parse.py` are out of scope.

## R1. What moves to the domain (`app/domain/call_analysis.py`)

- **Decision**: the module is standard library only and holds:
  - **`build_prompt(common, proc, transcript, agent_name)`**: moved **verbatim** from `calls_api.py`.
  - **`transcript_from_turns(turns)`**: `[{"index": i, "speaker_role": speaker, "human_transcript": text} for i, (speaker, text) in enumerate(turns, 1)]`.
  - **`agent_name_from_metadata(metadata)`**: `((metadata.get("agent") or {}).get("metadata") or {}).get("agent_name")`.
  - **`clean_answer(text)`**: `re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()`.
  - **`parse_answer(cleaned)`**: `json.loads` or `None` on `ValueError`.
  - **Errors**: `CallNotFound(call_id)` and `NoTranscript(call_id)`, whose `str()` is exactly today's message.
- **Rationale**: these are the rules (FR-003, FR-004, FR-008). Moving `build_prompt` verbatim is what keeps dry-run responses byte-identical (SC-001).

## R2. Ports and the use case

- **Decision**: three ports in `app/application/ports.py`:

  | Port | Methods | Raises |
  | --- | --- | --- |
  | `CallAnalysisSource` | `async load(call_id) -> CallToAnalyze \| None` and `async turns(call_id) -> list[tuple[str, str]]` | — |
  | `PromptTemplateSource` | `async load() -> dict` | `RulesUnavailable(path)`, with message `missing rules file: <path> (set RULES_DIR)` |
  | `LanguageModel` | `async ask(prompt, model: str \| None) -> tuple[str, str]` | `ModelUnavailable(reason)`, with message `could not get an answer from Ollama: <reason>` |

  The two port errors live in `ports.py`, because they are part of the port contracts.

  `AnalyzeCall(calls, template, model).execute(call_id, model_name=None, dry_run=False)` runs in this order, as today:
  1. load the call; `CallNotFound` if there is none;
  2. use the raw transcript, else `turns()`, which is only queried when needed; `NoTranscript` if both are empty;
  3. `template.load()`;
  4. `build_prompt`;
  5. with dry run, return `PromptPreview(id, external_id, call_type, prompt)`;
  6. otherwise `model.ask` → `clean_answer` → `parse_answer` → `ModelAnalysis(id, external_id, call_type, model, result, raw)`.
- **Rationale**: the same order means the same error precedence (404 before 422 before 503). One use case behind three narrow ports.
- **Alternative considered**: a single "analysis gateway" port. Rejected: it would mix persistence, file and model concerns.

## R3. Adapters

- **`SqlAlchemyCallAnalysisSource`** (`adapters/persistence/call_analysis_source.py`): today's two queries, moved:
  - `Call` joined with `Procedure.rules` by ID;
  - `CallTurn.speaker, text` ordered by `idx`.

  It maps the rows to `CallToAnalyze(id, external_id, call_type, metadata, raw_transcript, rules)`.
- **`JsonPromptTemplate(rules_dir)`** (`adapters/files/prompt_template.py`): reads `rules_dir / "_common.json"` on each `load()`, as today. `FileNotFoundError` becomes `RulesUnavailable(exc.filename)`. Other errors, such as invalid JSON, still propagate, as today (the user accepted this).
- **`OllamaModel(host, default_model, timeout, urlopen=urllib.request.urlopen)`** (`adapters/llm/ollama.py`):
  - **`normalize_host(host)`**: adds `http://` when the scheme is missing.
  - **`build_request(host, name, prompt)`**: the same payload and headers as today.
  - **`ask`**: runs the blocking call with `asyncio.to_thread`, as `run_in_threadpool` does today, but without importing FastAPI into the adapter. `URLError`, `OSError`, `KeyError` and `ValueError` become `ModelUnavailable(str(exc))`.
- **Testing**:
  - the persistence adapter with a fake session;
  - the template with tmp files and the real `docs/procedures/schema3`;
  - the model with an injected fake `urlopen` (stand-in model, SC-003), checking the request URL, payload and timeout, and the error mapping.

## R4. Settings at the outer edge

- **Decision**: `app/infrastructure/analysis_settings.py` has `analysis_adapters_from_env(environ) -> tuple[JsonPromptTemplate, OllamaModel]`:
  - `RULES_DIR` or the default `<repo>/docs/procedures/schema3` (the same path `calls_api` computed);
  - `OLLAMA_HOST` (default `http://localhost:11434`);
  - `OLLAMA_MODEL` (default `deepseek-r1:8b`);
  - `float(OLLAMA_TIMEOUT or 600)`.

  `main.configure_analysis(app, environ)` stores both adapters on `app.state` at import.
- **Rationale**: FR-009, and the same pattern as `configure_clock`.
- **Behavior note**: a non-numeric `OLLAMA_TIMEOUT` now stops the API from starting. Today it gives a 503 on each non-dry-run request. This is consistent with FR-009, which reads settings at startup, and with how `DEMO_TODAY` is handled.

## R5. HTTP adapter

- **Decision**: `app/adapters/http/analyze.py` holds the router and these pieces:
  - **`AnalyzeRequest(BaseModel)`**: `model: str | None = None`, `dry_run: bool = False`, unchanged.
  - **`get_analyze_call(request, session)`**: builds `AnalyzeCall(SqlAlchemyCallAnalysisSource(session), request.app.state.prompt_template, request.app.state.language_model)`.
  - **`@router.post("/calls/{call_id}") async def analyze_call(call_id: int, body: AnalyzeRequest | None = None, use_case = Depends(...))`**: runs the use case and maps errors: `CallNotFound` → 404, `NoTranscript` → 422, `RulesUnavailable` and `ModelUnavailable` → 503, each with `str(exc)` as the detail.
  - **`present_analysis(result)`**: produces exactly today's dicts.
- **Rationale**: a thin handler (FR-011) with an identical contract (FR-001, FR-006, FR-008).

## R6. Removing calls_api.py

- **Decision**:
  - delete `backend/app/calls_api.py`;
  - `main.py` includes `adapters.http.analyze.router` in its place;
  - `docs/procedures/schema3/README.md` line 43 now names `backend/app/adapters/http/analyze.py`, and says the prompt is built in `backend/app/domain/call_analysis.py`;
  - a test asserts that importing `app.calls_api` fails.

## R7. Proving "unchanged"

- **Decision**: before any code change, save the baseline with the current code:
  - the HTTP dry-run bodies for one call per call type (IDs 1, 2, 3, 4, 6, 8, 14, 15);
  - the 404 body for ID 999999;
  - the 503 body with `RULES_DIR` pointing at an empty folder.

  The baseline comes from the API running on port 8001 against the main database, and is saved to the scratchpad. After the change, the same requests must give byte-identical bodies and status codes.

  The 422 case cannot be reproduced with the stored data, because every call has a transcript. It is covered by use-case and route tests.
