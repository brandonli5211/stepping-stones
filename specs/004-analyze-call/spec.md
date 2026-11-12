# Feature Specification: Analyze a Call

**Feature Branch**: `feat/33-load-demo-48`

**Created**: 2026-11-11

**Status**: Draft

**Input**: User description: "Feature C — AnalyzeCall (issue #33). Analyzing a call builds the coaching prompt for one stored call from its transcript (or its turns when no raw transcript is stored), its procedure rules and the shared prompt template. It either returns the prompt (dry run) or asks the local language model and returns its parsed answer. Bring it into Clean Architecture compliance with the same request, response, status codes and messages. Settings are read only at the outer edge; a missing rules file still answers 503 at request time. Delete the old module once everything has moved and update the docs line that names it. The model is not running locally, so verify with dry-run responses byte-identical before and after, the not-found and no-transcript cases, and fake-model tests. Exactly one use case: AnalyzeCall."

**Primary use case**: AnalyzeCall (one use case for this feature). It completes the compliance work on the analysis module, as committed in feature 003's plan.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preview the coaching prompt for a call (Priority: P1)

A developer or analyst asks for a dry run of one stored call by its ID. They get the exact prompt that would go to the model: the procedure's steps and fields, the numbered transcript, and the expected output format. The model is not called.

**Why this priority**: the dry run is how prompts are checked today, and it is the only path that can be verified without a running model. It must stay exactly the same.

**Independent Test**: record dry-run responses for several stored calls before the change, then request them again afterwards. Each response is byte-identical.

**Acceptance Scenarios**:

1. **Given** a stored call with a transcript, **When** a dry run is requested, **Then** the response contains the call's ID, external ID, call type and the prompt, identical to the response before the change.
2. **Given** a stored call whose raw transcript is empty but whose turns are stored, **When** a dry run is requested, **Then** the transcript is rebuilt from the turns in order, numbered from 1, and the prompt uses it.
3. **Given** a call ID that does not exist, **When** analysis is requested, **Then** the answer is "not found" with the message `no call with id <id>`.
4. **Given** a stored call with neither a transcript nor turns, **When** analysis is requested, **Then** the answer is "unprocessable" with the message `call <id> has no transcript stored`.
5. **Given** the shared rules file is missing, **When** analysis is requested, dry run included, **Then** the answer is "service unavailable" with the message `missing rules file: <path> (set RULES_DIR)`. The service itself keeps running.

---

### User Story 2 - Get the model's judgment for a call (Priority: P2)

A developer asks for a full analysis of one call. The prompt goes to the local model, optionally with a model name chosen per request. The answer comes back with any reasoning block removed, and as parsed structured data when it is valid. The raw text is returned too.

**Why this priority**: this is the feature's real purpose, but it depends on a model that is not running in this environment. It is verified with a stand-in model.

**Independent Test**: with a stand-in model that returns a fixed answer, the response contains the call's identity, the model name, the parsed answer and the cleaned raw text. A stand-in that fails gives "service unavailable".

**Acceptance Scenarios**:

1. **Given** the model answers `<think>…</think>{"a": 1}`, **When** analysis runs, **Then** the response has `result` `{"a": 1}`, `raw` `{"a": 1}` and `model` set to the model that answered.
2. **Given** the model answers text that is not valid JSON, **When** analysis runs, **Then** `result` is empty and `raw` holds the cleaned text.
3. **Given** a model name in the request, **When** analysis runs, **Then** that model is asked. Otherwise the configured default is asked (`deepseek-r1:8b` unless set).
4. **Given** the model cannot be reached or its reply is malformed, **When** analysis runs, **Then** the answer is "service unavailable" with the message `could not get an answer from Ollama: <reason>`.

---

### Edge Cases

- **Request with no body**: treated as `{model: none, dry_run: false}`, as today.
- **Turn numbering**: transcript turns use their own `index` when present, otherwise their position from 1. Rebuilt turns are always numbered from 1, by position.
- **Agent name**: taken from the call's metadata (`agent.metadata.agent_name`). It is "unknown" when absent.
- **Which steps appear in the prompt**: only steps with no sub-checks, or with a confirmation-evidence sub-check, as today.
- **Logged values**: the logged values and the assigned task are never put in the prompt.
- **Model address without a scheme**: `localhost:11434` is treated as `http://localhost:11434`.
- **Slow model**: the request waits up to the configured timeout (600 s by default). Other requests are not blocked meanwhile.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Analysis MUST accept a call ID in the path and an optional body `{model?: text, dry_run?: boolean (default false)}`, unchanged.
- **FR-002**: It MUST load the call's ID, external ID, call type, metadata, raw transcript and procedure rules. A missing call MUST answer 404 with `no call with id <id>`.
- **FR-003**: When the raw transcript is empty, it MUST rebuild one from the stored turns in turn order, as entries of index (from 1), speaker role and text. When both are empty, it MUST answer 422 with `call <id> has no transcript stored`.
- **FR-004**: The prompt MUST be built exactly as today from:
  - the shared template;
  - the procedure's gate question, its eligible steps (FR edge cases) and its fields;
  - the numbered transcript;
  - the agent name;
  - the output example.
- **FR-005**: The shared template MUST be read from `_common.json` in the rules folder: `RULES_DIR`, or the project's `docs/procedures/schema3` by default. It is read when a request is handled. A missing file MUST answer 503 with `missing rules file: <path> (set RULES_DIR)`.
- **FR-006**: With `dry_run` true, the response MUST be `{id, external_id, call_type, prompt}` and the model MUST NOT be called.
- **FR-007**: Otherwise the model MUST be asked:
  - at the configured address (`OLLAMA_HOST`, default `http://localhost:11434`, scheme added when missing);
  - with the requested or default model (`OLLAMA_MODEL`, default `deepseek-r1:8b`);
  - with JSON output, temperature 0 and seed 42;
  - within the configured timeout (`OLLAMA_TIMEOUT` seconds, default 600).

  It MUST be asked without blocking other requests. Connection, OS, missing-key and value errors MUST answer 503 with `could not get an answer from Ollama: <reason>`.
- **FR-008**: The answer MUST have every `<think>…</think>` block removed, across lines, and be trimmed. The response MUST be `{id, external_id, call_type, model, result, raw}`, where `result` is the parsed JSON, or empty when parsing fails.
- **FR-009**: The settings `RULES_DIR`, `OLLAMA_HOST`, `OLLAMA_MODEL` and `OLLAMA_TIMEOUT` MUST be read only at the outer edge of the system, when the service starts.
- **FR-010**: The rules for prompt building, transcript fallback, agent name and answer cleaning MUST be computable and testable without a database, web server or model.
- **FR-011**: The analysis request handler MUST only translate the request and response, including error codes, and delegate.
- **FR-012**: The old module that held this endpoint (`backend/app/calls_api.py`) MUST be removed, and documentation that names it MUST point to the new location.
- **FR-013**: The calls list (feature 003) and the demo results command (feature 002) MUST keep working unchanged.

### Key Entities

- **Call to analyze**: ID, external ID, call type, metadata, raw transcript and procedure rules.
- **Transcript turn**: index, speaker role, and the human transcript or the machine transcript.
- **Shared template**: the prompt template and field types (`_common.json`).
- **Model answer**: the name of the model that answered and its raw text. After cleaning: the raw text and the parsed result.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For at least 5 stored calls, one of each call type present, dry-run responses are byte-identical before and after the change.
- **SC-002**: Not-found and no-transcript requests give the same status codes and messages as before.
- **SC-003**: With a stand-in model, a full analysis returns the parsed answer, the cleaned raw text and the model name. A failing stand-in gives "service unavailable" with the reason.
- **SC-004**: Every rule in FR-003, FR-004 and FR-008 has an automated test that runs without a database, web server or model.
- **SC-005**: After the change no module named `calls_api` remains, and the full test suite and the feature 002 and 003 checks still pass.

## Assumptions

- A local model is not running in this environment. The live call is verified only through a stand-in model and through the dry run, which builds the identical prompt.
- These settings are read once at startup instead of on every request. That changes nothing in practice, because the process environment does not change while the service runs.
- The rules file itself is still read on each request, so the 503 behavior holds.
- The model client keeps using the standard library, so no new dependency is added.
- `load_calls.py` and `call_parse.py` are out of scope and are tracked as a separate issue.
- No current call has an empty raw transcript. The turn-rebuild and no-transcript paths are covered by automated tests, with a stand-in data source.
