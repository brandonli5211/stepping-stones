# Implementation Plan: Analyze a Call

**Branch**: `feat/33-load-demo-48` (issue #33) | **Date**: 2026-11-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-analyze-call/spec.md`

This plan closes the governance item recorded in feature 003's Complexity Tracking. Once it is done, `backend/app/calls_api.py` no longer exists, so every file this PR touches complies with the constitution.

## Summary

**Primary use case**: `AnalyzeCall`. For one stored call it builds the coaching prompt from the call's transcript (or its stored turns), its procedure rules and the shared template. It then returns either that prompt (dry run) or the cleaned and parsed answer of the language model.

`POST /calls/{call_id}` keeps its request, responses, status codes and messages. The prompt builder moves verbatim into the domain, together with the transcript fallback, the agent-name lookup and the answer cleaning.

**Inward dependency path**:

| Layer | Module | What it holds |
| --- | --- | --- |
| Domain | `app/domain/call_analysis.py` | Pure rules and errors. Standard library only. |
| Application | `app/application/analyze_call.py` | The use case. Depends on the domain and on three ports in `app/application/ports.py`: `CallAnalysisSource`, `PromptTemplateSource` and `LanguageModel`. |
| Adapters | `persistence/call_analysis_source.py` | Async SQLAlchemy reads. |
| Adapters | `files/prompt_template.py` | `_common.json`, read on each request. |
| Adapters | `llm/ollama.py` | Standard-library HTTP client, run off the event loop. |
| Adapters | `http/analyze.py` | The thin `async` route and error mapping. |
| Infrastructure | `infrastructure/analysis_settings.py` + `main.py` | Reads `RULES_DIR` and `OLLAMA_*` at startup. |

`calls_api.py` is deleted.

## Use Cases

*Accurate after Phase 0 (research) and after Phase 1 (design).*

| Use case | Responsibility | Module |
| --- | --- | --- |
| `AnalyzeCall` (primary) | Loads one call through `CallAnalysisSource`, picks its transcript, loads the shared template through `PromptTemplateSource`, and builds the prompt. It returns the prompt for a dry run, or else asks `LanguageModel` and returns the cleaned and parsed answer. It never reads the environment, parses HTTP, runs SQL or opens sockets. | `backend/app/application/analyze_call.py` |

**Out of scope for this plan**:
- `load_calls.py` and `call_parse.py` (the synchronous psycopg loader and the seed scoring): a separate issue, per the user.
- Saving model results to `call_steps`: not done today, and not added here.

## Technical Context

**Language/Version**: Python ≥ 3.12. The host runs 3.13 via uv.

**Primary Dependencies**: FastAPI and pydantic (existing, used for the body model), async SQLAlchemy 2, and the standard library `urllib`, `json`, `re` and `asyncio`. There are no new dependencies.

**Storage**: PostgreSQL 18. Reads only from `calls`, `procedures` and `call_turns`. No schema change.

**Testing**: pytest with no database and no model:
- the domain;
- the use case with fakes;
- the source with a fake session;
- the template with tmp and real files;
- the Ollama adapter with a fake `urlopen`;
- the settings;
- the route and error mapping.

Real behavior is checked through byte-identical dry runs and the 404 and 503 responses ([quickstart.md](quickstart.md)).

**Target Platform**: The local API.

**Project Type**: Web application backend.

**Performance Goals**: Unchanged. The model call stays off the event loop.

**Constraints**:
- **Identical contract**: the request, the responses and the messages stay as they are.
- **Prompt moved verbatim**: `build_prompt` is moved without edits.
- **Settings at startup**: settings are read only in the composition root.
- **Missing rules file**: still a 503 at request time.
- **Ollama not available**: verification uses the dry run and a stand-in model.

**Scale/Scope**: one use case, about 7 new modules, an edited `main.py`, `ports.py` and docs README, one deleted module, 6 tasks or fewer.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Before research | After design |
| --- | --- | --- |
| I. Server owns the judgment | Pass. The model is asked by the backend. Nothing moves to React, and nothing is scored here. | Pass. |
| II. Asynchronous API | Pass. The route stays `async def`. | Pass. The blocking HTTP call to Ollama runs via `asyncio.to_thread`, so the event loop is not blocked. |
| III. Asynchronous persistence | Pass. Reads use `AsyncSession`. | Pass. `SqlAlchemyCallAnalysisSource` uses `AsyncSession` only. |
| IV. Typed component UI | Pass. No frontend change. | Pass. |
| V. One stack | Pass. No new packages, and the client stays on `urllib`. | Pass. |
| VI. Unit test every new function | Pass (planned). Moved functions count as changed, so they are tested. | Pass. Every function in [data-model.md](data-model.md) and every adapter, setting and route function has a calling test. |
| VII. Clean Architecture | Pass. One use case, three ports. The rules move out of the router module. | Pass. The domain is standard library only. The use case imports only the domain and ports. Adapters do not import infrastructure. An import guard covers `fastapi`, `sqlalchemy`, `alembic`, `psycopg`, `os` and `urllib` for the domain and application. |
| Workflow | Pass. Same branch and issue (#33). One use case is in the Summary and in Use Cases. | Pass. Planned as one slice of 6 tasks or fewer. |
| Governance: touched non-compliant files | Pass. `calls_api.py` is removed, so feature 003's conditional gate closes. `main.py`, `ports.py` and the docs README are compliant. | Pass. |

No gate failed. Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/004-analyze-call/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/post-call-analysis.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code

```text
backend/
├── app/
│   ├── domain/call_analysis.py                      # NEW  build_prompt (verbatim), transcript_from_turns, agent_name_from_metadata,
│   │                                                 #      clean_answer, parse_answer, CallToAnalyze/PromptPreview/ModelAnalysis, errors
│   ├── application/
│   │   ├── ports.py                                 # EDIT CallAnalysisSource, PromptTemplateSource, LanguageModel, RulesUnavailable, ModelUnavailable
│   │   └── analyze_call.py                          # NEW  AnalyzeCall
│   ├── adapters/
│   │   ├── persistence/call_analysis_source.py      # NEW
│   │   ├── files/prompt_template.py                 # NEW  JsonPromptTemplate
│   │   ├── llm/__init__.py, llm/ollama.py           # NEW  OllamaModel, normalize_host, build_request
│   │   └── http/analyze.py                          # NEW  AnalyzeRequest, route, present_analysis, get_analyze_call
│   ├── infrastructure/analysis_settings.py          # NEW  analysis_adapters_from_env
│   ├── main.py                                      # EDIT configure_analysis; include analyze router; drop calls_api
│   └── calls_api.py                                 # DELETE
├── tests/                                           # NEW  test_domain_call_analysis, test_analyze_call, test_call_analysis_source,
│                                                    #      test_prompt_template, test_ollama, test_analysis_settings, test_analyze_route
docs/procedures/schema3/README.md                    # EDIT line naming calls_api.py
```

**Structure Decision**: the same layering as features 001–003. `adapters/llm/` is the first adapter package for an external service.

## Complexity Tracking

No constitution violations require justification.

## Phase 0 and Phase 1 outputs

- **Phase 0**: [research.md](research.md), decisions R1–R7.
- **Phase 1**:
  - [data-model.md](data-model.md)
  - [contracts/post-call-analysis.md](contracts/post-call-analysis.md)
  - [quickstart.md](quickstart.md)

**Post-design constitution check**: all gates pass, and the Use Cases section lists exactly one primary use case after both phases.
