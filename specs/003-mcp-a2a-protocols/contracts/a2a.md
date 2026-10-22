# Contract: A2A agent `lonekrav-advisor`

The agent speaks A2A v1.0 over JSON-RPC 2.0, with SSE for streaming (a2a-sdk 1.2.3, research R7).

| What | Where |
|---|---|
| Agent card | `GET http://localhost:8000/.well-known/agent-card.json` |
| JSON-RPC endpoint | `POST http://localhost:8000/a2a`, header `A2A-Version: 1.0` |
| Methods | `SendMessage`, `SendStreamingMessage`, `GetTask`, `CancelTask` (v1.0 names; `message/stream` is the 0.3 name and is not enabled) |

## Card

- `name`: `lonekrav-advisor`. `version`: the package version.
- `description`: what the advisor does, plus the disclosure that input goes to a third-party model
  service (OpenRouter).
- `supported_interfaces`: `[{url: "http://localhost:8000/a2a", protocol_binding: "JSONRPC", protocol_version: "1.0"}]`.
- `capabilities.streaming`: `true`.
- `default_input_modes` and `default_output_modes`: `text/plain` and `application/json`.
- `skills`: one skill, with `id: "honest-fit-memo"`.

## Input (one user message)

The preferred form is one data part, a JSON object validated as `AdvisorRequest`:

```json
{"ad": "<job ad text>", "background": "<optional>",
 "offer": {"monthly_salary_sek": 52000, "fte_percent": 100, "application_type": "first_permit",
           "filed_on": "2026-10-01"}}
```

Text parts alone are also accepted. The model then reads the offer out of the text, and the
eligibility tool validates it. If both forms are present, the data part is used and the text is
added to the background. Every message is an independent task (FR-011a).

## Streamed events (`SendStreamingMessage`)

The events arrive in this order:

1. `task`, with state `TASK_STATE_SUBMITTED`.
2. `statusUpdate` `TASK_STATE_WORKING` "Reading the job ad".
3. For each tool call:
   - `statusUpdate` `WORKING` "Calling <tool>".
   - On success, `artifactUpdate` named `ui_sync:<tool>` with one data part:
     ```json
     {"kind": "ui_sync", "tool": "get_occupation_salary", "args": {"code": "2512"},
      "result": { /* the tool's full result, e.g. SalaryPayload */ }}
     ```
4. `artifactUpdate` named `memo`, with one `text/markdown` text part.
5. `statusUpdate` `TASK_STATE_COMPLETED`.

`SendMessage` returns the same task once it has finished, with the same artifacts.

## Terminal states

| State | When | Message text |
|---|---|---|
| `TASK_STATE_COMPLETED` | a memo was produced | none (the memo is an artifact) |
| `TASK_STATE_REJECTED` | there is no `OPENROUTER_KEY` | `Agent unavailable: no model key is configured (set OPENROUTER_KEY in .env).` |
| `TASK_STATE_FAILED` | the data part is invalid, the round limit was hit, or the model timed out or erred | a short cause, e.g. `Invalid input: offer.fte_percent ...` or `Stopped after 8 tool rounds without a memo.` |
| `TASK_STATE_CANCELED` | the client sent `CancelTask` | none |

## Memo rules (FR-016, research R10)

- The memo lists every plausible code with its threshold, pass or fail result and warnings. It
  says that the code must match the real duties, and it never suggests a code because its threshold
  is lower.
- All figures and legal dates come from tool results in the same task. Sources and checked-on dates
  are cited.
- It always contains the core `HONEST_FIT` text and a not-legal-advice statement, and it ends with
  the third-party notice. `finalise_memo` adds any of these that the model leaves out.
