---
description: "Task list for Feature 003: Lönekrav over MCP and A2A"
---

# Tasks: Lönekrav over MCP and A2A

**Input**: `specs/003-mcp-a2a-protocols/` (spec.md, plan.md, research.md, data-model.md,
contracts/mcp.md, contracts/a2a.md, quickstart.md, checklists/protocols.md)

**Tests**: required. Constitution Principle IV mandates red/green TDD: run every test task and see
it fail for the stated reason before its implementation task starts.

**Fixtures**: the default run stays offline. It uses `fixture_engine`, `salaries` and `api_client`
from `tests/conftest.py`, with fixture codes 0110, 1211, 1212, 2421, 2512, 3511, 4430, 5322, 5343
and 9210. The advisor runs against a scripted `FakeModel`, and only `-m live` calls OpenRouter.

**Legal literals**: no amount, percentage or legal date may appear in new code or tests. Tests read
them from the registry or compare with REST responses (FR-004).

**Working examples**: `references/fastmcp_mount.py` and `references/a2a_server_client.py`, copied
in T002, are the patterns to follow (research R2–R7).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1–US3 from spec.md

---

## Phase 1: Setup

- [X] T001 Run `uv add "fastmcp>=4.1.3,<5" "a2a-sdk[fastapi]>=1.2.3,<2" "openai>=3.36.1,<4" python-dotenv`. Register the `live` marker in `[tool.pytest.ini_options]` and add `and not live` to the default `addopts` in `pyproject.toml`. Then run `rtk proxy uv run pytest -q`, which must still report 264 passed
- [X] T002 [P] Copy the research examples from the scratchpad to `references/fastmcp_mount.py` and `references/a2a_server_client.py`, each with a header docstring that says what it proves and how to run it. Point to them from CLAUDE.md in T035

---

## Phase 2: Foundational (blocks every story)

### The shared service (FR-002)

- [X] T003 Write the test `tests/unit/test_service.py` over `fixture_engine` and `salaries`. It covers each `Service` method in data-model.md:
  - `occupation("2512")` has `legal_flags` and no `ilo_isco08` description, and `occupation("9999")` raises `UnknownCode`.
  - `salary("2512")` defaults `on` to today and carries the Swedish and English titles. An unknown age band raises `ValueError`, and an unknown code raises `UnknownCode`.
  - `compare` with one unknown code raises `UnknownCode` naming it.
  - `eligibility` with an unknown code raises `UnknownCode`.
  - `parse_ad(AdText(text=...))` equals `adparse.parse(..., engine.embedders["kblab"])`.
  - `timeline()` equals `load_registry().timeline()`.
- [X] T004 Move `AdText` from `src/lonekrav/api/v1.py` to `src/lonekrav/core/adparse.py`. Implement `src/lonekrav/core/service.py` (a frozen dataclass `Service` and its seven methods) until T003 passes
- [X] T005 Refactor `src/lonekrav/app.py` and `src/lonekrav/api/v1.py`:
  - The lifespan builds `app.state.service = Service(...)`.
  - The routes call `request.app.state.service`.
  - One app exception handler maps `UnknownCode` to a 404 with `{"detail": str(e)}`.
  - The salary route keeps its `ValueError` to 422 mapping.
  - `/health` reads `service.engine`.
  - Remove `_known` and `_profile`.
  
  `tests/integration/test_api.py` must pass unchanged (FR-001)

---

## Phase 3: User Story 1 — a chat assistant uses Lönekrav's tools (P1) 🎯 MVP

**Goal**: five tools and two resources at `/mcp`, each equal to its REST route (contracts/mcp.md).

**Independent test**: `uv run pytest tests/integration/test_mcp.py`, then quickstart §3 against a
running server.

- [X] T006 [US1] Write the test `tests/integration/test_mcp.py`. Its fixture runs `create_app(...)` under `TestClient` (for the lifespan) and opens `fastmcp.Client(app.state.mcp)` in memory. It checks that `list_tools` names exactly the five tools, each with a description and with input and output schemas, and that `list_resources` and `list_resource_templates` give `legal://timeline` and `ssyk://{code}`. Run it and see it fail
- [X] T007 [US1] Implement `src/lonekrav/protocols/__init__.py` and `src/lonekrav/protocols/mcp_server.py` (`build_mcp(app) -> FastMCP`, built with `mask_error_details=True`; tools and resources as in contracts/mcp.md, each a one-line call into `app.state.service`; `UnknownCode` and `ValueError` re-raised as `ToolError(str(e))`). In `create_app`, set `app.state.mcp`, combine the lifespans with `combine_lifespans`, and mount `mcp.http_app(path="/mcp")` at `/` last (research R2). Work until T006 passes
- [X] T008 [US1] Add parity tests to `tests/integration/test_mcp.py` (SC-001). Each tool's `structured_content` must equal the `api_client` JSON for the same input, using the same inputs as `test_api.py`:
  - search in fast mode, with and without `parse_ad`
  - `extract_job_ad_signal`
  - salary for 2512, with and without an age band and a date
  - eligibility, using the `OFFER` from `test_api.py`
  - compare 2512 and 2421, with and without an offer
  
  Each resource's JSON text must equal the matching REST route (timeline, and the occupation 2512 without ILO text). Run it red if anything differs, then fix it in `mcp_server.py`
- [X] T009 [US1] Add error tests to `tests/integration/test_mcp.py` (FR-009):
  - An unknown code in salary, eligibility, compare and `ssyk://9999` gives `is_error` with REST's detail text.
  - An unknown age band gives REST's 422 message.
  - A 20 001-character ad and `k=21` are rejected with errors that name the field.
  - A tool that raises `RuntimeError("/secret/path")` gives a masked message without "secret".
  - The server keeps serving afterwards.
- [X] T010 [US1] Add a test to `tests/integration/test_mcp.py` (FR-005): with `caplog` at DEBUG, call search with the text `"PRIVATE-AD-TEXT"` and eligibility with salary 41234, and check that neither appears in the logs. Also add an HTTP-level test: with `TestClient(app)`, POST an MCP `initialize` request to exactly `/mcp`, which must answer 200 and not redirect, and check that `/api/v1/health` still answers 200
- [X] T011 [US1] Run quickstart §3 by hand. Start `uv run lonekrav-serve`, run `claude mcp add --transport http lonekrav http://localhost:8000/mcp` (local scope), then `claude mcp list`, then `claude -p ...` calling `search_occupations` and `get_occupation_salary`. Save the commands, the tool list, the answer and the time taken to `references/mcp-claude-code.md` (FR-021a)

**Checkpoint**: MCP works with no key. This is the MVP.

---

## Phase 4: User Story 2 — the advisor writes an honest-fit memo (P2)

**Goal**: `lonekrav-advisor` streams progress, `ui_sync` artifacts and a guarded memo (contracts/a2a.md).

**Independent test**: `uv run pytest tests/unit/test_advisor.py tests/unit/test_agent_loop.py tests/integration/test_a2a.py`.

- [X] T012 [P] [US2] Write the test `tests/unit/test_advisor.py`:
  - `AdvisorRequest` accepts `{ad}` alone, and a full request with an offer whose salary is a float such as `52000.0`.
  - It rejects an empty ad, a 20 001-character ad, a background over 5 000 characters, and an offer that `Offer` rejects.
  - `finalise_memo` adds `HONEST_FIT` only when it is absent, adds `DISCLAIMER` only when "not legal advice" is absent, adds the no-results line when `tools_called` is empty, and always ends with `THIRD_PARTY_NOTICE`.
  - Running `finalise_memo` twice gives the same memo as running it once.
- [X] T013 [US2] Implement `src/lonekrav/core/advisor.py` (`AdvisorRequest`, `THIRD_PARTY_NOTICE`, `finalise_memo`) until T012 passes
- [X] T014 [US2] Write the test `tests/unit/test_agent_loop.py`. A `FakeModel` replays scripted `Reply`s and records the messages and tools it received. A fake `tools` object has `specs()` and `async call(name, args) -> (is_error, payload)`. Cover:
  - (a) A search call, then a salary call, then a memo. The events are `Progress`, `ToolResult(search)`, `Progress`, `ToolResult(salary)`, `Memo`, and the memo has passed through `finalise_memo`.
  - (b) A tool error goes back to the model as that tool's message and yields no `ToolResult`.
  - (c) Arguments that are not JSON are reported to the model as an error.
  - (d) A model that never stops raises `RoundLimit` after `MAX_ROUNDS` calls.
  - (e) A model exception propagates.
  - (f) The first two messages are the system prompt and a user message holding the ad, the background and the offer fields.
  - (g) A text-only request is passed through as the user message.
- [X] T015 [US2] Implement `src/lonekrav/protocols/agent/__init__.py` and `src/lonekrav/protocols/agent/loop.py` (data-model.md, "Advisor events" and "ChatModel"):
  - `SYSTEM_PROMPT` (the honest-fit voice, with no figures)
  - `Reply`, `Progress`, `ToolResult`, `Memo` and `RoundLimit`
  - `MAX_ROUNDS = 8`
  - `McpTools(mcp)`: `specs()` from `list_tools` (research R6), and `call` through `fastmcp.Client(mcp, raise_on_error=False)`, which returns `structured_content`
  - `openrouter_model(key, model)` over `AsyncOpenAI(timeout=30, max_retries=1)`
  - `run()`
  
  Work until T014 passes. Confirm that `test_no_legal_literal_outside_the_registry` covers `SYSTEM_PROMPT`: plant a literal in it once, watch the test fail, then remove the literal
- [X] T016 [US2] Write the test `tests/integration/test_a2a.py`. Build `create_app(..., chat_model=FakeModel(script))` under `TestClient`.
  - `GET /.well-known/agent-card.json` has the name `lonekrav-advisor`, `capabilities.streaming` true, one skill, input modes `text/plain` and `application/json`, an interface URL ending `/a2a` with protocol version `1.0`, and the third-party disclosure in the description.
  - A raw `SendStreamingMessage` POST to `/a2a` (header `A2A-Version: 1.0`) with a data part `{ad, offer}` gives the SSE events in the order in contracts/a2a.md.
  - Each `ui_sync` artifact's `result` equals the matching MCP tool result.
  - The memo artifact is `text/markdown` and contains `HONEST_FIT`.
  - The last state is `TASK_STATE_COMPLETED`.
  
  Run it and see it fail
- [X] T017 [US2] Implement `src/lonekrav/protocols/agent/executor.py` (`AdvisorExecutor`):
  - Enqueue the Task first.
  - Take the data part as an `AdvisorRequest`, adding any text parts to `background`; otherwise use the text alone.
  - Map the events with `TaskUpdater` as in data-model.md.
  - Turn `ValidationError` into a failed state naming the fields and rules but not the values.
  - Turn `RoundLimit`, timeouts and API errors into a failed state with a short cause.
  - Implement `cancel`.
  
  Then implement `src/lonekrav/protocols/a2a_server.py` (`CARD` and `add_a2a(app, mcp, chat_model)`, as in research R7), and wire it in `create_app`, which gains `chat_model=None` and calls it before the MCP mount. Work until T016 passes
- [X] T018 [US2] Add to `tests/integration/test_a2a.py`:
  - An invalid offer (`fte_percent: 0`) gives `TASK_STATE_FAILED` naming `fte_percent`, and the model is never called.
  - A model that loops gives `FAILED` with the round-limit text.
  - A model that raises gives `FAILED` without the exception's internals.
  - A blocking `SendMessage` returns the same final task.
  - `CancelTask` on a running task (the fake model waits on an event) gives `TASK_STATE_CANCELED`.
  - Two concurrent streamed runs both complete (FR-018).
  - Two messages with the same `contextId` run independently: the second run's model receives exactly the system and user messages (FR-011a).
- [X] T019 [US2] Add a logging test to `tests/integration/test_a2a.py` (FR-005): with `caplog` at DEBUG, run a streamed message whose ad is `"PRIVATE-AD-TEXT"` and whose salary is 41234, plus one run that fails validation, and check that neither value, nor the `OPENROUTER_KEY` value (set to a sentinel), appears in the logs or in the failed-state text (FR-014)
- [X] T020 [P] [US2] Write `tests/integration/test_a2a_live.py` (`@pytest.mark.live`). It is skipped unless `OPENROUTER_KEY` is in the environment or in `.env`, read with `dotenv_values`. It runs the real model over the fixture app with a short English ad and an offer, and checks for at least one `ui_sync` artifact, a memo containing `HONEST_FIT` and `THIRD_PARTY_NOTICE`, and `COMPLETED`. Run `uv run pytest -m live`
- [X] T021 [US2] Write `scripts/a2a_stream.py`:
  - It takes `--url` (default `http://localhost:8000`), `--ad` or `--ad-file`, `--background` and `--offer` (JSON).
  - It fetches the card with `A2ACardResolver` and streams with `ClientFactory(ClientConfig(streaming=True))`.
  - For each event it prints the time since the start, its kind, its state or artifact name, and the part kinds; it prints the memo in full and `ui_sync` results shortened.
  - At the end it prints the total time and the model time (total minus the time spent in tool calls, taken from the event gaps).
  
  Run it against a live server and save the output to `references/a2a-stream.md` (FR-021b, SC-006)

**Checkpoint**: the advisor works end to end with a fake model and a real one.

---

## Phase 5: User Story 3 — works without a key (P3)

**Goal**: no key means the card is served and messages are rejected, and everything else works (FR-017).

**Independent test**: `uv run pytest -k no_key`, then quickstart §2.

- [X] T022 [US3] Add tests to `tests/integration/test_a2a.py`. With `monkeypatch.delenv("OPENROUTER_KEY")` and `create_app(...)` with no `chat_model`:
  - The card is served.
  - A streamed message ends in `TASK_STATE_REJECTED` with the text "Agent unavailable" and `OPENROUTER_KEY`, within one second.
  - An MCP tool call and `/api/v1/health` succeed.
  
  Also test that `create_app` picks `openrouter_model` when the key is set (monkeypatched, without calling it), and that the key's value never appears in the card. Run the tests and see them fail
- [X] T023 [US3] In `create_app`, set `chat_model = openrouter_model(key, os.environ.get("LONEKRAV_LLM_MODEL", DEFAULT_MODEL))` if `OPENROUTER_KEY` is set and otherwise `None`. In `main()`, call `load_dotenv()`. Make `AdvisorExecutor` reject when the model is `None`. Work until T022 passes
- [X] T024 [US3] Run quickstart §2 by hand with no key in the environment, and append the output to `references/a2a-stream.md` under "Without a key"

---

## Phase 6: Polish and cross-cutting

- [X] T025 Regenerate `references/api-smoke.md` with `scripts/api_smoke.py` against a live server, and diff it against the committed file. Only timestamps may differ (FR-001)
- [X] T026 [P] Run `rtk proxy uv run pytest -q` (the new total, all passing), `uv run pytest -m benchmark -q` (9 passed, with the server stopped), `uv run pytest -m live -q` and `uv run ruff check src tests scripts`
- [X] T027 [P] Check `src/lonekrav/protocols/` against Principle I. Every function must only validate, call `Service` or the loop, and serialise. Move any rule found there into `core/`, test-first
- [X] T028 [P] Measure the advisor's latency over three live runs of the quickstart §4 ad, recording the total time and the model's share, and add the results to `references/a2a-stream.md` (SC-006)
- [ ] T029 Update `references/development-plan.md` §003 for the actual decisions: fastmcp 4.1.3, `SendStreamingMessage`, the rejected state, Haiku 5.5 as the default, and the in-memory MCP client in the agent
- [ ] T030 [P] Write `docs/walkthroughs/003-mcp-a2a-protocols.md` with the walkthrough skill (snippets emitted from disk)
- [ ] T031 Run `/speckit-converge` and complete any tasks it appends
- [ ] T032 Read the whole diff, then open the PR. It should include the test totals, the two transcripts, the latency figures, and a note that the handoff's `message/stream` is `SendStreamingMessage` in v1.0
- [ ] T033 Read every Copilot review comment on the PR, fix each valid one with a red/green test, and reply in each thread with the fix commit
- [ ] T034 Remove the scratchpad virtual environment, and keep the local-scope `lonekrav` MCP entry only if the maintainer wants it
- [ ] T035 Compound step: add "Things worked out in Feature 003" to CLAUDE.md (the mount order and lifespan, ToolError and masking, the protobuf integers-as-floats issue, Task-first enqueueing, the in-memory MCP client as the agent's tool bus, and the reference files), and update the memory status file

---

## Dependencies

- Setup (T001–T002) comes before Foundational (T003–T005). Foundational comes before all stories.
- US1 (T006–T011) depends only on Foundational.
- US2 needs US1's `build_mcp`, because the agent calls the tools through it (research R6). T012–T013 can start in parallel with US1.
- US3 needs US2's executor and card (T017).
- Polish comes after all stories. T031 comes before T032, and T032 before T033.

## Parallel examples

- After T005: T006 (MCP tests) and T012 (advisor model tests) touch different files.
- In US2: T020 (the live test) can be written while T018 and T019 are in progress.
- In Polish: T026, T027, T028 and T030 run side by side.

## Implementation strategy

1. MVP: Setup, Foundational and US1. Lönekrav is then usable from Claude Code with no key and no cost.
2. Add US2, the advisor with a fake model first and then live.
3. Add US3, the no-key rejection, which is small but gates startup on a fresh machine.
4. Polish, evidence, PR and the Copilot review.
