# Research: Lönekrav over MCP and A2A

Everything in this file was run on 2026-10-22, in a scratch virtual environment with the pinned
versions. The two working examples are copied to `references/` in the first implementation task.

## R1 Library versions

**Decision**: `fastmcp>=4.1.3,<5` (which brings mcp 2.3.0), `a2a-sdk[fastapi]>=1.2.3,<2`,
`openai>=3.36.1,<4`, and `python-dotenv` for reading `.env` in `main()` only. The lockfile pins
the exact versions.

**Rationale**: these were the newest versions on PyPI on 2026-10-22. The development plan named
fastmcp 4.1.2, but 4.1.3 is a patch release. All of them resolve alongside the project's starlette
1.9.0 and pydantic 2.14.1.

**Alternatives**: the low-level `mcp` server, which needs more code than FastMCP for the same five
tools; and a hand-written JSON-RPC A2A server, which would re-implement a whole protocol.

## R2 Mounting FastMCP at exactly `/mcp`

**Decision**: `mcp_app = mcp.http_app(path="/mcp")`, then `app.mount("/", mcp_app)` as the last
thing registered. The FastAPI lifespan is
`combine_lifespans(own_lifespan, mcp_app.lifespan)` (`fastmcp.utilities.lifespan`).

**Evidence** (TestClient POST of an `initialize` request):

| Mount | `/mcp` | `/mcp/` | `/mcp/mcp` |
|---|---|---|---|
| `mount("/mcp", http_app(path="/"))` | 307 | 200 | 404 |
| `mount("/mcp", http_app())` | 307 | 404 | 200 |
| `mount("/", http_app(path="/mcp"))` | **200** | 307 | 404 |

The third row is the only one that serves exactly `/mcp`, which is the URL that
`claude mcp add --transport http lonekrav http://localhost:8000/mcp` uses. The session manager
starts only when the combined lifespan runs (`with TestClient(app)`). A root mount swallows any route
registered after it, so it has to go last.

## R3 How tools reach the loaded data

**Decision**: `build_mcp(app)` creates the FastMCP server in a closure. Each tool reads
`app.state.service` when it is called.

**Rationale**: `get_http_request()` works only over HTTP. It raises in the in-memory client, which
the tests and the advisor (R6) both use. It also returns the mounted sub-app, not the FastAPI app.
The closure works over both transports.

## R4 Tool signatures, results and errors

**Decision**:
- Each tool that has a core request model takes it as its one argument: `request: SearchRequest`,
  `request: EligibilityRequest`, `request: CompareRequest` and `request: AdText`. `AdText` moves
  from `api/v1.py` to `core/adparse.py`.
- `get_occupation_salary` takes flat arguments `code`, `age_band` and `on`, because REST takes them
  as path and query parameters and has no request model.
- Tools return the core result models.
- Expected failures (an unknown code, an unknown age band) raise `fastmcp.exceptions.ToolError`
  with the same text as REST's 404 or 422 detail.
- The server is built with `mask_error_details=True`, so unexpected exceptions do not leak paths.
  REST already does the same in its 500 handler.

**Evidence**:
- A pydantic argument nests in the input schema (`{"request": {...}}`) and keeps every field
  constraint, such as the 20 000-character limit and the four-digit code pattern. That satisfies
  FR-008 without copying any constraint.
- The output schema is published in `list_tools`.
- `structured_content` is the model as a JSON dict, so it can be compared directly with the REST
  JSON (SC-001).
- A `ToolError` message reaches the client unchanged. A plain exception's message is masked.
- Sync tools run in an AnyIO worker thread, as sync FastAPI routes do. The Harrier lock therefore
  still covers the first full-mode search.

## R5 Resources

**Decision**: `legal://timeline` returns `[e.model_dump(mode="json") for e in timeline]`, and
`ssyk://{code}` returns `profile.model_dump(mode="json")`, both as `application/json`.

**Evidence**: in fastmcp 4.1.3 a resource cannot return a pydantic model. A single model fails
with "contents must be str, bytes, or list[ResourceContent]", and a list of models with "not JSON
serializable". A JSON dict or list works.

## R6 How the advisor calls the tools

**Decision**: the advisor calls the five tools through `fastmcp.Client(mcp)`, using the
in-memory transport and `raise_on_error=False`. The tool list it gives the model is built from
`list_tools()`: each tool becomes
`{"type": "function", "function": {"name", "description", "parameters": input_schema}}`.

**Rationale**: FR-013 asks for "the same five operations as the tool server, with the same schemas,
backed by the same shared functions". Going through the MCP server meets that by construction:
there is one set of tool definitions, and nothing can drift. A failed call gives `is_error` and the
error text, which go back to the model as the tool message. A successful call gives the result,
which becomes the `ui_sync` item.

**Alternative**: a second registry of plain Python functions with schemas from
`model_json_schema()`. It is the same idea in two places, so it was rejected.

## R7 A2A server (a2a-sdk 1.2.3)

**Decision**:
- `DefaultRequestHandler(agent_executor=AdvisorExecutor(...), task_store=InMemoryTaskStore(), agent_card=CARD)`.
- `add_a2a_routes_to_fastapi(app, agent_card_routes=create_agent_card_routes(CARD), jsonrpc_routes=create_jsonrpc_routes(handler, rpc_url="/a2a"))`.
- These routes are registered before the MCP root mount.

**Evidence** (a real uvicorn run, read with the SDK client and with raw httpx):
- The card is served at `/.well-known/agent-card.json`.
- The card has no top-level `url`. The endpoint goes in
  `supported_interfaces=[AgentInterface(url=..., protocol_binding="JSONRPC", protocol_version="1.0")]`,
  and `ClientFactory` picks the URL from there. The URL is absolute, so it is
  `http://localhost:8000/a2a`, the address `lonekrav-serve` binds. Changing it for Docker belongs
  to 004.
- The A2A v1.0 JSON-RPC method names are `SendMessage`, `SendStreamingMessage`, `GetTask` and
  `CancelTask`. The handoff's `message/stream` is the 0.3 name and is accepted only with
  `enable_v0_3_compat=True`, which is not used here. The evidence transcript uses
  `SendStreamingMessage`, and `quickstart.md` says so.
- Types are protobuf. Data parts are `google.protobuf.Value`, so integers arrive as floats (52000 →
  52000.0). Pydantic's lax mode accepts a float with no fraction for an `int` field, so
  `AdvisorRequest` validation is unaffected, and the UI sees ordinary JSON numbers.
- The executor has to enqueue a `Task` (`new_task_from_user_message`) before its first status
  update, or the handler raises. After a terminal state, `TaskUpdater` refuses further updates.
- The streamed event order seen was `Task SUBMITTED`, then `Status WORKING`, then artifacts
  `ui_sync:*` (data), then artifact `memo` (text), then `Status COMPLETED`.
- In-process test pattern: `[e async for e in handler.on_message_send_stream(SendMessageRequest(...), ServerCallContext())]`.

## R8 Without a key

**Decision**: with no key the advisor ends the task with `TaskUpdater.reject(...)` and the text
"Agent unavailable: no model key is configured (set OPENROUTER_KEY in .env)." The card is served
as usual.

**Rationale**: A2A's `rejected` state means the agent declined the task. That is accurate here,
because nothing broke, and a UI can tell it apart from `failed`, which means a run went wrong.

## R9 Model client and default model

**Decision**:
- A single `AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=key, timeout=30,
  max_retries=1)` is created in the app factory when the key is present. It is not created lazily,
  so there is no race to guard against (FR-018).
- The model comes from `LONEKRAV_LLM_MODEL` and defaults to `anthropic/claude-haiku-5.5`.
- The loop stops after `MAX_ROUNDS = 8` model calls.
- `main()` loads `.env` with python-dotenv. `create_app` reads only `os.environ`, so tests stay
  hermetic.

**Evidence**: OpenRouter price list and a probe on 2026-10-22. Each model got 3 runs of one
`search_occupations` call with a job sentence.

| Model | $/M in | $/M out | Correct tool call | Latency (s) |
|---|---|---|---|---|
| anthropic/claude-haiku-5.5 | 0.10 | 0.50 | 3/3 | 1.80, 1.11, 1.01 |
| google/gemini-3.1-flash-lite | 0.25 | 1.50 | 3/3 | 0.61, 0.69, 0.75 |
| deepseek/deepseek-v4-flash | 0.09 | 0.18 | 3/3 | 4.59, 2.39, 2.06 |
| openai/gpt-5-nano | 0.05 | 0.40 | 3/3 | 4.41, 5.28, 7.75 |

Haiku 5.5 is the cheapest model that answers in about 1 s. It is also the most likely of these to
follow the honest-fit instructions. Gemini Flash Lite is faster but costs 2.5–3× more per token.

## R10 Honest-fit guard and personal data

**Decision**:
- The disclosure text (`THIRD_PARTY_NOTICE`), the advisor input model (`AdvisorRequest`) and the
  guard `finalise_memo(memo, tools_called)` live in `core/advisor.py`.
- The guard adds the core `HONEST_FIT` text if the memo does not contain it. It adds `DISCLAIMER` if
  the memo makes no not-legal-advice statement. If no tool was called, it adds a line saying the
  memo is not based on any Lönekrav result. It always ends the memo with `THIRD_PARTY_NOTICE`.
- The system prompt is a Python string constant, so the existing
  `test_no_legal_literal_outside_the_registry` scan covers it (FR-004).

**Rationale**: model wording varies. A deterministic guard in core makes SC-004 testable without
depending on the model.

## R11 Logging

The a2a-sdk and fastmcp loggers are left at the app's default level, `INFO`. A test sends a
private marker through MCP and A2A with logging captured at `DEBUG` and checks that the marker
never appears (FR-005). The marker is the same one the REST test uses. FastMCP logs a traceback
for each `ToolError`. That traceback holds the error text only, which is a code or a band, never
request content.
