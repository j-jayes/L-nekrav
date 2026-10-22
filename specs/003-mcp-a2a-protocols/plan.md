# Implementation Plan: Lönekrav over MCP and A2A

**Branch**: `003-mcp-a2a-protocols` | **Date**: 2026-10-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-mcp-a2a-protocols/spec.md`

## Summary

Feature 003 serves the existing core over two more protocols on the same FastAPI app. FastMCP
serves five tools and two resources at `/mcp`. An A2A v1.0 agent, `lonekrav-advisor`, has its card
at `/.well-known/agent-card.json` and its JSON-RPC endpoint at `/a2a`. Research settled four things:

- The small rules that sit in `api/v1.py` today move to `core/service.py`, so all three adapters
  call the same functions (FR-002).
- The advisor calls its tools through an in-memory FastMCP client, so its tools are the MCP tools
  by construction (R6).
- A2A v1.0's streaming method is `SendStreamingMessage`; `message/stream` is the 0.3 name (R7).
- The default model is `anthropic/claude-haiku-5.5`, chosen for price and an answer time of about
  1 s (R9).

## Technical Context

**Language/Version**: Python 3.12 (uv-managed)

**Primary Dependencies**: the 002 stack plus `fastmcp` 4.1.3, `a2a-sdk[fastapi]` 1.2.3, `openai`
3.36 (an OpenAI-compatible client pointed at OpenRouter) and `python-dotenv` (R1)

**Storage**: none new. A2A tasks live in memory (`InMemoryTaskStore`) and are lost on restart
(spec Assumptions).

**Testing**:
- pytest runs offline by default. MCP tests use `fastmcp.Client(mcp)` in memory over the
  `fixture_engine` and `salaries` fixtures, and compare each result with `api_client` for the same input.
- A2A tests drive `DefaultRequestHandler.on_message_send_stream` with a scripted fake model, plus
  TestClient tests for the card and the JSON-RPC route.
- One live test under a new `live` marker is skipped without `OPENROUTER_KEY`.

**Target Platform**: a local single process (`lonekrav-serve` on 127.0.0.1:8000). Docker comes in 004.

**Project Type**: a web service (one FastAPI app, three protocol surfaces)

**Performance Goals**:
- The tools add no measurable time to the core calls.
- A live advisor run is measured, but has no target yet (SC-006). Model latency is about 1 s per
  round (R9).
- A no-key reply takes under 1 s (SC-005).

**Constraints**:
- No domain logic in `protocols/` (Principle I).
- No legal literal anywhere outside the registry (FR-004).
- No request content in logs (FR-005).
- The key comes only from the environment, or from `.env` in `main()`.

**Scale/Scope**: single tenant, a handful of concurrent advisor runs, five tools, two resources
and one agent skill.

## Constitution Check

*GATE: checked before research, and again after design.*

| Principle | How the design complies |
|---|---|
| I. Core first, adapters thin | `core/service.py` holds the not-found check, the ILO stripping, the salary date default and the salary titles. `core/advisor.py` holds the advisor input model, the honest-fit guard and the third-party notice. `api/v1.py`, `protocols/mcp_server.py` and `protocols/a2a_server.py` only validate, call and serialise. `core` imports no transport framework. |
| II. Data integrity | Tools return the core models unchanged, so sources, tables, `is_simulated` and checked-on dates pass straight through (FR-003). The system prompt is a Python constant covered by the legal-literal scan, and the memo takes its figures from tool results (FR-004). |
| III. Honest fit | The system prompt sets the honest-fit voice. `finalise_memo` adds `HONEST_FIT`, `DISCLAIMER` and the third-party notice when the model leaves them out, so the guarantee does not rest on the model (FR-016, R10). |
| IV. Test first, proven by hand | Each tool, resource and advisor behaviour gets a failing test first. The evidence is the two transcripts, from Claude Code and from the A2A client, plus a regenerated `api-smoke.md` (FR-021). |
| V. Compact and portable | The app still serves one port. Without the key the advisor rejects tasks with a clear message, and everything else works (FR-017, R8). No new services. |
| VI. Simplicity | There is one set of tool definitions, and the advisor reuses it (R6). The model client is created eagerly, so nothing needs a lock. Only one new setting is added, `LONEKRAV_LLM_MODEL`, and the spec asks for it. |

Result: pass. The one judgement call is recorded under Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/003-mcp-a2a-protocols/
├── plan.md  research.md  data-model.md  quickstart.md
├── contracts/mcp.md  contracts/a2a.md
├── checklists/requirements.md
└── tasks.md            # /speckit-tasks
```

### Source Code (repository root)

```text
src/lonekrav/
├── app.py                    # create_app(..., chat_model=None): service, MCP mount, A2A routes, combined lifespan
├── api/v1.py                 # now calls core.service; unchanged responses
├── core/
│   ├── service.py            # NEW: Service(engine, profiles, distributions, age_bands) and its 7 operations
│   ├── advisor.py            # NEW: AdvisorRequest, THIRD_PARTY_NOTICE, finalise_memo
│   └── adparse.py            # AdText moves here from api/v1.py
└── protocols/
    ├── __init__.py
    ├── mcp_server.py         # NEW: build_mcp(app) -> FastMCP (5 tools, 2 resources)
    ├── a2a_server.py         # NEW: CARD, add_a2a(app, mcp, chat_model)
    └── agent/
        ├── __init__.py
        ├── loop.py           # NEW: SYSTEM_PROMPT, ChatModel protocol, openrouter_model(), run() async generator
        └── executor.py       # NEW: AdvisorExecutor(AgentExecutor): parts -> run() -> TaskUpdater events
tests/
├── integration/test_mcp.py         # tools/resources == REST, errors, logging
├── integration/test_a2a.py         # card, SendStreamingMessage over TestClient, no-key reject, logging
├── integration/test_a2a_live.py    # @pytest.mark.live, skipped without the key
├── unit/test_service.py            # the moved rules
├── unit/test_advisor.py            # AdvisorRequest, finalise_memo
└── unit/test_agent_loop.py         # fake model: order, ui_sync, round limit, model error, tool error
scripts/a2a_stream.py               # evidence: fetch the card, stream a message, print the events
references/
├── fastmcp_mount.py  a2a_server_client.py   # working examples from research (R2–R7)
├── mcp-claude-code.md  a2a-stream.md         # evidence (FR-021)
```

**Structure Decision**: the package keeps its single-project layout. `protocols/` is new, as the
development plan says. The new domain-facing code goes in `core/`, following Principle I.

## Design notes

- **App wiring**: `create_app` builds the FastAPI app with
  `lifespan=combine_lifespans(load_state, mcp_app.lifespan)`. `load_state` puts
  `app.state.service = Service(...)`. The wiring order is: REST router first, then `add_a2a(...)`,
  then `app.mount("/", mcp_app)`, which must come last (R2).
- **chat_model**: `create_app(chat_model=...)` takes a fake in tests. Otherwise it is
  `openrouter_model()` when `OPENROUTER_KEY` is set, and `None` when it is not.
- **REST mapping**: `UnknownCode` becomes a 404 through one app-level exception handler. The
  unknown-age-band `ValueError` stays a 422 in the salary route. The detail strings stay the same.
  `references/api-smoke.md` regenerated must not differ, except in timestamps.
- **Advisor run**: `run(request, model, tools)` sends a system prompt and a user message rendered from
  `AdvisorRequest` (or the raw text). Then it loops up to `MAX_ROUNDS` times:
  - It calls the model.
  - For each tool call, it yields `Progress(f"Calling {name}")`, calls the tool through the MCP
    client, yields `ToolResult(name, args, result)` on success, and appends the tool message.
    An error's text goes to the model, not to a `ui_sync` item.
  - When there are no tool calls, it yields `Memo(finalise_memo(text, called))`.
  - Past the limit it raises `RoundLimit`.
- **Executor**: it enqueues the Task first. With no model it rejects (R8). Otherwise it validates the
  data part, or takes the text parts, and maps `Progress` to a working status, `ToolResult` to a
  `ui_sync` artifact and `Memo` to a `memo` artifact, then completes. If validation fails, it
  fails with the pydantic message before any model call. A `RoundLimit`, model timeout or API error
  fails the task with a short cause and no request content.

## Complexity Tracking

| Judgement call | Why | Simpler alternative rejected because |
|---|---|---|
| The agent's tool loop sits in `protocols/agent/`, not `core/` | It orchestrates a model and the protocol's tools. It holds no SSYK, salary or legal rule; those, and the guard, live in `core/advisor.py`. The development plan places it there too. | Putting it in `core/` would make core import the openai client and fastmcp's in-memory client. That breaks Principle I's no-transport-framework rule. |
