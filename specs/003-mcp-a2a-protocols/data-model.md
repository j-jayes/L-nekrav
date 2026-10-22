# Data Model: Lönekrav over MCP and A2A

Feature 003 adds no stored data. Every result the protocols return is an existing core model
(`SearchAnswer`, `ParsedAd`, `SalaryPayload`, `EligibilityAnswer`, `Comparison`, `TimelineEvent`,
`OccupationProfile`), as 002 defines them. This file covers only the new types.

## Service (`core/service.py`)

A frozen dataclass holding what the app's lifespan loads. It has one method per operation and
replaces the rules that sit in `api/v1.py` today.

| Field | Type |
|---|---|
| `engine` | `SearchEngine` |
| `profiles` | `dict[str, OccupationProfile]` |
| `distributions` | `list[SalaryDistribution]` |
| `age_bands` | `list[AgeBandSalary]` |

| Method | Returns | Raises |
|---|---|---|
| `search(req: SearchRequest)` | `SearchAnswer` | none |
| `parse_ad(req: AdText)` | `ParsedAd` (uses `engine.embedders["kblab"]`) | none |
| `salary(code, on=None, age_band=None)` | `SalaryPayload`; `on` defaults to today, and the titles come from the profile | `UnknownCode`; `ValueError` for an unknown age band |
| `eligibility(req: EligibilityRequest)` | `EligibilityAnswer` | `UnknownCode` |
| `compare(req: CompareRequest)` | `Comparison` | `UnknownCode` for the first unknown code |
| `occupation(code)` | `OccupationProfile` with registry `legal_flags`, without ILO text | `UnknownCode` |
| `timeline()` | `list[TimelineEvent]` | none |

## AdText (moved from `api/v1.py` to `core/adparse.py`)

`text: str`, 1 to 20 000 characters. REST and MCP both use it.

## AdvisorRequest (`core/advisor.py`)

| Field | Type | Rule |
|---|---|---|
| `ad` | `str` | 1 to 20 000 characters, the same limit as `AdText` |
| `background` | `str \| None` | at most 5 000 characters |
| `offer` | `Offer \| None` | the eligibility `Offer` (everything except the code), with its validators |

A2A data parts deliver integers as floats (research R7). Lax validation accepts `52000.0` for an
`int` field.

## Memo guard (`core/advisor.py`)

`finalise_memo(memo: str, tools_called: list[str]) -> str` returns the memo with any missing
pieces added, in this order:
1. `HONEST_FIT` (from `core.search`), unless the memo already contains it.
2. If `tools_called` is empty, a line saying the memo rests on no Lönekrav result.
3. `DISCLAIMER` (from `core.eligibility`), unless the memo already contains "not legal advice".
4. `THIRD_PARTY_NOTICE`, always, as the final line.

## Advisor events (`protocols/agent/loop.py`)

`run()` yields these three events. The executor maps each one to an A2A event.

| Event | Fields | A2A event |
|---|---|---|
| `Progress` | `text` | status update `TASK_STATE_WORKING` with an agent message |
| `ToolResult` | `tool`, `args`, `result` (the tool's `structured_content`) | artifact `ui_sync:<tool>` with one data part, `{"kind": "ui_sync", "tool", "args", "result"}` |
| `Memo` | `text` (after `finalise_memo`) | artifact `memo` with one `text/markdown` part |

### Task states

```text
submitted ──► working ──► completed      (memo artifact sent)
    │            └──────► failed         (invalid input, round limit, model timeout or error)
    │            └──────► canceled       (client CancelTask)
    └──────────────────► rejected        (no model key: "Agent unavailable: ...")
```

## ChatModel (`protocols/agent/loop.py`)

`async (messages: list[dict], tools: list[dict]) -> Reply`.
`Reply` is `content: str | None` plus `tool_calls: list[(id, name, arguments_json)]`.
`openrouter_model()` wraps `AsyncOpenAI.chat.completions.create`. Tests pass a scripted fake.
