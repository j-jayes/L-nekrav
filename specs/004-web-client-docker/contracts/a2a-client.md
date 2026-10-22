# Contract: the browser's A2A client (`frontend/src/lib/a2aClient.ts`)

The server side is `specs/003-mcp-a2a-protocols/contracts/a2a.md`. This file covers what the page
sends and how it reads the reply. The field names are confirmed against the bytes captured in
`references/a2a-sse-wire.md` before the parser is written (R7).

## Send

`POST /a2a`, with the headers `Content-Type: application/json`, `Accept: text/event-stream` and
`A2A-Version: 1.0`. The body is JSON-RPC 2.0 with method `SendStreamingMessage`. Its params hold a
`message` with a new `messageId`, role user, and one data part `{ad, background?, offer?}`. The
offer is the shared draft, sent only if the user ticks "include my offer".

## Read

The response body is SSE. Events are separated by a blank line, and each one's `data:` lines are
joined and parsed as a JSON-RPC response. A `result` holds exactly one of a task, a status update or
an artifact update. The client yields:

| Event | When | Page action |
|---|---|---|
| `task` | the first event | store `taskId` |
| `status` (`state`, text) | each status update | append the progress text; on a final state (`COMPLETED`, `FAILED`, `REJECTED`, `CANCELED`) end the run |
| `ui_sync` (`tool`, `args`, `result`) | an artifact named `ui_sync:<tool>` | update the selection (plan "Advisor → chart") |
| `memo` (markdown) | the artifact named `memo` | render it |
| `error` (message) | a JSON-RPC `error`, an HTTP error or a broken stream | the run state becomes `failed` or `lost` and shows the message |

## Cancel

`POST /a2a` with method `CancelTask` and `{id: taskId}`, then abort the fetch. The run ends
`canceled` when the server confirms it, or when the abort completes.
