---

description: "Task list for AnalyzeCall (issue #33)"
---

# Tasks: Analyze a Call

**Input**: Design documents from `/specs/004-analyze-call/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/post-call-analysis.md, quickstart.md, constitution.md (1.5.0)

**Tests**: Required by constitution VI and by spec FR-010 and SC-004. Each task ships unit tests for every function it adds or moves, and each test calls the function and asserts its result or its specified failure. The tests need no database and no model. The real database is checked in T006 through quickstart.md.

**Organization**: ONE Clean Architecture use case, `AnalyzeCall` (plan.md Summary), as a single vertical slice of 6 tasks. Spec stories US1 (the prompt preview) and US2 (the model's judgment) are both served by this one slice.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: `[US1]` = the single use-case slice
- Paths are relative to the repository root

## Use Case: AnalyzeCall (from plan.md Summary)

**Goal**: `POST /calls/{call_id}` is served by a thin async route, then the `AnalyzeCall` use case, then the domain rules and three ports. The settings are read once in `main.py`, and `calls_api.py` is gone.

**Independent Test**: [quickstart.md](quickstart.md) steps 1–4:
1. `uv run test` is green.
2. The 8 dry runs, the 404 and the 503 are byte-identical to the baseline.
3. No `calls_api` module or reference remains.
4. `GET /calls` is unchanged.

- [X] T001 [US1] **Baseline and domain.**
  - **Baseline first, before any code change** (research R7). Start the *current* API with `uv run uvicorn app.main:app --port 8001` against the main database. Save each body and status code with `curl -s -w '\n%{http_code}'` to the scratchpad's `baseline_c/` directory:
    - `POST /calls/{id}` with `{"dry_run": true}` for IDs 1, 2, 3, 4, 6, 8, 14 and 15;
    - `POST /calls/999999` with `{"dry_run": true}`;
    - `GET /calls`;
    - `POST /calls/1` with `{"dry_run": true}`, after restarting the API with `RULES_DIR=<empty scratch dir>`.
  - Then create `backend/app/domain/call_analysis.py` (standard library only) with:
    - frozen dataclasses `CallToAnalyze(id, external_id, call_type, metadata, raw_transcript, rules)`, `PromptPreview(id, external_id, call_type, prompt)` and `ModelAnalysis(id, external_id, call_type, model, result, raw)`;
    - exceptions `CallNotFound(call_id)` with `str` `no call with id <id>`, and `NoTranscript(call_id)` with `str` `call <id> has no transcript stored`;
    - `build_prompt(common, proc, transcript, agent_name)`, **copied verbatim** from `backend/app/calls_api.py`;
    - `transcript_from_turns(turns)`: `[(speaker, text), …]` → `[{"index": i, "speaker_role": speaker, "human_transcript": text}]`, numbered `i` from 1;
    - `agent_name_from_metadata(metadata)`: `((metadata.get("agent") or {}).get("metadata") or {}).get("agent_name")`;
    - `clean_answer(text)`: `re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()`;
    - `parse_answer(cleaned)`: `json.loads`, or `None` on `ValueError`.
  - **Tests** in `backend/tests/test_domain_call_analysis.py`:
    - `build_prompt` with the real `docs/procedures/schema3/_common.json` and `transfer_money.json` and a two-turn transcript: it includes the gate question, only eligible steps, every field, numbered turns, and the agent name or `unknown`; it leaves no `{{` placeholders; it uses `index` when present and position otherwise; it falls back to the machine text;
    - `build_prompt` gives the same output as `app.calls_api.build_prompt`, while that module still exists (the test is removed in T005);
    - `transcript_from_turns` numbering;
    - `agent_name_from_metadata` when present, missing and nested missing;
    - `clean_answer` with several `<think>` blocks across lines;
    - `parse_answer` with valid JSON and with invalid JSON;
    - the two error messages;
    - an import guard: no `fastapi`, `sqlalchemy`, `alembic`, `psycopg`, `os`, `urllib` or `app`.

- [X] T002 [US1] **Application.**
  - Add to `backend/app/application/ports.py`:
    - `CallAnalysisSource` (`async load(call_id) -> CallToAnalyze | None`, `async turns(call_id) -> list[tuple[str, str]]`);
    - `PromptTemplateSource` (`async load() -> dict`);
    - `LanguageModel` (`async ask(prompt, model: str | None) -> tuple[str, str]`);
    - the exceptions `RulesUnavailable(path)`, with `str` `missing rules file: <path> (set RULES_DIR)`, and `ModelUnavailable(reason)`, with `str` `could not get an answer from Ollama: <reason>`.
  - Create `backend/app/application/analyze_call.py` with frozen `AnalyzeCall(calls, template, model)`. Its `async execute(call_id, model_name=None, dry_run=False)` runs in this order:
    1. `load`, raising `CallNotFound` when there is no call;
    2. `raw_transcript`, else `transcript_from_turns(await turns(call_id))` (only then is `turns` called), raising `NoTranscript` when empty;
    3. `template.load()`;
    4. `build_prompt(common, call.rules, transcript, agent_name_from_metadata(call.metadata))`;
    5. with dry run, return `PromptPreview`;
    6. otherwise `model.ask(prompt, model_name)`, then `clean_answer`, then `parse_answer`, returning `ModelAnalysis`.
  - **Tests** in `backend/tests/test_analyze_call.py`, with fakes:
    - a dry run returns the preview and never asks the model;
    - the fallback to turns is used only when the raw transcript is empty;
    - 404 comes before 422, and 422 comes before the template is loaded;
    - `RulesUnavailable` propagates even on a dry run;
    - the stand-in model answering `<think>x</think>{"a": 1}` gives `result {"a": 1}` and `raw '{"a": 1}'`;
    - non-JSON gives `result None`;
    - `model_name` is passed through;
    - `ModelUnavailable` propagates;
    - an import guard for `analyze_call.py` and `ports.py`: no `fastapi`, `sqlalchemy`, `alembic`, `psycopg`, `os` or `urllib`, and nothing from `app.adapters` or `app.infrastructure`.

- [X] T003 [US1] **Adapters.**
  - `backend/app/adapters/persistence/call_analysis_source.py`: `SqlAlchemyCallAnalysisSource(session)`.
    - `load` selects `Call.id, external_id, call_type, raw_metadata, raw_transcript, Procedure.rules`, joined to `Procedure`, `where Call.id == call_id`, and maps the row to `CallToAnalyze` or returns `None`.
    - `turns` selects `CallTurn.speaker, CallTurn.text` for that call, ordered by `idx`.
  - `backend/app/adapters/files/prompt_template.py`: `JsonPromptTemplate(rules_dir)`. Its `async load()` returns `json.loads((rules_dir / "_common.json").read_text())`. It turns `FileNotFoundError` into `RulesUnavailable(exc.filename)`; other errors propagate.
  - `backend/app/adapters/llm/__init__.py` and `backend/app/adapters/llm/ollama.py`:
    - `normalize_host(host)` adds `http://` when the address contains no `://`;
    - `build_request(host, name, prompt)` builds a `urllib.request.Request` to `host.rstrip("/") + "/api/generate"` with the payload `{"model", "prompt", "stream": False, "format": "json", "options": {"temperature": 0, "seed": 42}}` and the header `Content-Type: application/json`;
    - `OllamaModel(host, default_model, timeout, urlopen=urllib.request.urlopen)` with `async ask(prompt, model)`. It uses `name = model or default_model`, runs the blocking call via `asyncio.to_thread`, which opens the request with `timeout` and returns `json.load(resp)["response"]`, and returns `(name, answer)`. It turns `urllib.error.URLError`, `OSError`, `KeyError` and `ValueError` into `ModelUnavailable(str(exc))`.
  - **Tests** in `backend/tests/test_call_analysis_source.py`, `test_prompt_template.py` and `test_ollama.py`:
    - the source, with a fake session: row mapping, `None` when missing, turns in order, and the compiled SQL;
    - the template: a tmp file loads; a missing file raises `RulesUnavailable` naming the full path; invalid JSON raises `ValueError`; the real schema3 folder loads;
    - Ollama, with a fake `urlopen` as the stand-in model:
      - the request URL, body and header, and the timeout passed through;
      - the answer is returned with the right model name, both default and override;
      - `normalize_host` cases;
      - each of the four errors becomes `ModelUnavailable` with its reason;
      - the fake `urlopen` records the thread it runs on, and the test asserts that thread is not the one running the event loop, so `ask` never blocks the loop (FR-007, analyze finding L1).
  - **Convergence 1 (Constitution VI, partial)**: add a test that calls `OllamaModel._ask_blocking` directly and asserts that:
    - it returns the reply's `response` text;
    - it opens the request with the configured timeout;
    - a reply without `response` raises `KeyError`.

- [X] T004 [US1] **Settings and composition.**
  - Create `backend/app/infrastructure/analysis_settings.py` with `DEFAULT_RULES_DIR = <repo>/docs/procedures/schema3`.
  - In that module, `analysis_adapters_from_env(environ) -> tuple[JsonPromptTemplate, OllamaModel]` returns:
    - `JsonPromptTemplate(Path(environ.get("RULES_DIR") or DEFAULT_RULES_DIR))`;
    - `OllamaModel(normalize_host(environ.get("OLLAMA_HOST", "http://localhost:11434")), environ.get("OLLAMA_MODEL", "deepseek-r1:8b"), float(environ.get("OLLAMA_TIMEOUT", "600")))`.

    A non-numeric timeout raises `ValueError`; the user approved this in R4.
  - In `backend/app/main.py`, add `configure_analysis(app, environ)`, which sets `app.state.prompt_template` and `app.state.language_model`, and call it at import, next to `configure_clock`.
  - **Tests** in `backend/tests/test_analysis_settings.py`:
    - the defaults; each variable overridden; an empty `RULES_DIR` falls back to the default;
    - a host without a scheme gets `http://` added;
    - a bad timeout raises;
    - `DEFAULT_RULES_DIR` exists and has `_common.json`;
    - `configure_analysis` on a fresh `FastAPI()` sets both attributes;
    - `app.main.app.state` has both after import.

- [X] T005 [US1] **HTTP adapter and removal of calls_api.py.**
  - Create `backend/app/adapters/http/analyze.py` with:
    - `AnalyzeRequest(BaseModel)`: `model: str | None = None`, `dry_run: bool = False`;
    - `present_analysis(result)`: a `PromptPreview` gives `{"id","external_id","call_type","prompt"}`, and a `ModelAnalysis` gives `{"id","external_id","call_type","model","result","raw"}`, in that key order;
    - `async get_analyze_call(request, session = Depends(get_session))`: builds `AnalyzeCall(SqlAlchemyCallAnalysisSource(session), request.app.state.prompt_template, request.app.state.language_model)`;
    - `@router.post("/calls/{call_id}") async def analyze_call(call_id: int, body: AnalyzeRequest | None = None, use_case = Depends(get_analyze_call)) -> dict`. It keeps the docstring `call_id is our own call id: the `id` that GET /calls returns.`, uses `body or AnalyzeRequest()`, and maps errors as `CallNotFound` → `HTTPException(404, str(e))`, `NoTranscript` → 422, and `RulesUnavailable` or `ModelUnavailable` → 503.
  - Delete `backend/app/calls_api.py`, and remove its import and `include_router` from `backend/app/main.py`, which now includes the analyze router.
  - Remove the temporary comparison test from T001.
  - Update `docs/procedures/schema3/README.md` line 43 to name `backend/app/adapters/http/analyze.py`, with the prompt built in `backend/app/domain/call_analysis.py`.
  - **Tests** in `backend/tests/test_analyze_route.py`, with a fake use case:
    - each result type is presented with its exact keys and order;
    - a missing body becomes a default request;
    - each error gives its status code with the exact detail;
    - the handler source has no `select(`, `session.`, `os.environ` or `urlopen`;
    - `get_analyze_call` wires the source and both state adapters;
    - `app.main.app` has `POST /calls/{call_id}` exactly once, still has `GET /calls`, and `import app.calls_api` raises `ModuleNotFoundError`.

- [X] T006 [US1] **Validate.**
  1. `uv run test` is green.
  2. Run the T001 requests against the new API on port 8001, including the `RULES_DIR` restart. Every body and status code must be byte-identical to `baseline_c/`: 8 × 200, then 404, then 503, plus `GET /calls`.
  3. Quickstart step 3: no `calls_api` file or reference remains in `backend/app` or `docs`.
  4. Record any mismatch rather than changing the expected output.

**Checkpoint**: `AnalyzeCall` works through the domain, application and ports, adapters, and composition layers. The route only delegates and maps errors. Settings are read only in `main.py`. `calls_api.py` is gone, and every new or moved function has a calling unit test.

---

## Dependencies & Execution Order

1. T001: baseline first, then the domain.
2. T002 depends on T001.
3. T003 depends on T002 (for the port errors).
4. T004 depends on T003.
5. T005 depends on T002–T004.
6. T006 depends on all of the above.

## Implementation Strategy

1. Implement T001→T006 in order. Each task includes its own tests, and `uv run test` must be green after each.
2. Stop when the independent test passes.
3. `load_calls.py` and `call_parse.py` are a separate issue.

## Notes

- 6 tasks, one use case. Hard ceiling respected.
- No schema change. No new dependencies.
- Commit when converged, per the user.
- **Convergence pass 1 (2026-11-11)**: converge found `_ask_blocking` with no direct calling test (Constitution VI, partial). Appending it as T007 would break the 6-task ceiling, so it was folded into T003, which was reopened.
