# A2A v1.0 on the wire: what the browser receives (Feature 004 research R7)

Captured on 2026-10-22 with `curl -N` against `uv run lonekrav-serve` (a2a-sdk 1.2.3). The request
is a `SendStreamingMessage` POST with `Content-Type: application/json`,
`Accept: text/event-stream` and `A2A-Version: 1.0`, and one data part `{ad, background, offer}`
(the public example ad `tests/fixtures/ads/en1_backend.txt`, a made-up offer). The raw bytes are
in `frontend/src/test/fixtures/a2a/` and `frontend/src/lib/a2aClient.test.ts` replays them.
This file was generated from those files; each event is cut to 240 characters.

What a client must handle, from these captures:

- Each SSE event is a single `data: ` line and a blank line, with CRLF line endings and no `event:` or `id:` field.
- Each data line is a JSON-RPC response whose `result` holds exactly one key: `task`,
  `statusUpdate` or `artifactUpdate`.
- The final state is only in `status.state` (`TASK_STATE_COMPLETED`, `_FAILED`, `_REJECTED`,
  `_CANCELED`). There is no `final` flag.
- The first `task` event echoes the user's message in `history`, so it carries the ad text.
- Artifacts are named `ui_sync:<tool>` (one `data` part) and `memo` (one `text` part with
  `mediaType: text/markdown`, `lastChunk: true`).
- Data parts are protobuf JSON, so integers arrive as floats (`52000.0`).
- A JSON-RPC error (here the 0.3 method name `message/stream`) comes back as HTTP 200 with
  `Content-Type: application/json`, not as SSE.
- `CancelTask {id}` answers with the task in `TASK_STATE_CANCELED`, and the open stream then
  ends with that state.

## A full run (with a key): `completed.sse`

```text
data: {"result": {"task": {"id": "a37cc001-e062-4fad-87c6-a9deab55a382", "contextId": "50d6e59d-cb13-4cc3-87c7-cef7d7e24f0b", "status": {"state": "TASK_STATE_SUBMITTED"}, "history": [{"messageId": "web-1", "contextId": "50d6e59d-cb13-4cc3-8…
data: {"result": {"statusUpdate": {"taskId": "a37cc001-e062-4fad-87c6-a9deab55a382", "contextId": "50d6e59d-cb13-4cc3-87c7-cef7d7e24f0b", "status": {"state": "TASK_STATE_WORKING", "message": {"messageId": "a4cf5fcc-9117-4ec3-9758-72ec608743…
data: {"result": {"statusUpdate": {"taskId": "a37cc001-e062-4fad-87c6-a9deab55a382", "contextId": "50d6e59d-cb13-4cc3-87c7-cef7d7e24f0b", "status": {"state": "TASK_STATE_WORKING", "message": {"messageId": "14cda7bf-be75-4138-836b-8397b25dbe…
data: {"result": {"artifactUpdate": {"taskId": "a37cc001-e062-4fad-87c6-a9deab55a382", "contextId": "50d6e59d-cb13-4cc3-87c7-cef7d7e24f0b", "artifact": {"artifactId": "b233ccda-ce7e-4a8c-8874-ac59996210b2", "name": "ui_sync:search_occupatio…
data: {"result": {"statusUpdate": {"taskId": "a37cc001-e062-4fad-87c6-a9deab55a382", "contextId": "50d6e59d-cb13-4cc3-87c7-cef7d7e24f0b", "status": {"state": "TASK_STATE_WORKING", "message": {"messageId": "101a300f-ca6b-4791-aca9-046e3a6998…
data: {"result": {"artifactUpdate": {"taskId": "a37cc001-e062-4fad-87c6-a9deab55a382", "contextId": "50d6e59d-cb13-4cc3-87c7-cef7d7e24f0b", "artifact": {"artifactId": "e73d1b46-60f9-4d93-851a-5d3bc5f4e7a0", "name": "ui_sync:compare_occupati…
data: {"result": {"artifactUpdate": {"taskId": "a37cc001-e062-4fad-87c6-a9deab55a382", "contextId": "50d6e59d-cb13-4cc3-87c7-cef7d7e24f0b", "artifact": {"artifactId": "ba72b409-74b1-428b-ba23-eeb36a04b523", "name": "memo", "parts": [{"text"…
data: {"result": {"statusUpdate": {"taskId": "a37cc001-e062-4fad-87c6-a9deab55a382", "contextId": "50d6e59d-cb13-4cc3-87c7-cef7d7e24f0b", "status": {"state": "TASK_STATE_COMPLETED", "timestamp": "2026-10-22T12:57:02.292996Z"}}}, "id": 1, "j…
```

## No key: rejected at once: `rejected.sse`

```text
data: {"result": {"task": {"id": "52d69030-93dc-471f-b388-27bc617a8bf0", "contextId": "b7d156e4-bf24-4450-bad1-2fe7f2c38611", "status": {"state": "TASK_STATE_SUBMITTED"}, "history": [{"messageId": "web-1", "contextId": "b7d156e4-bf24-4450-b…
data: {"result": {"statusUpdate": {"taskId": "52d69030-93dc-471f-b388-27bc617a8bf0", "contextId": "b7d156e4-bf24-4450-bad1-2fe7f2c38611", "status": {"state": "TASK_STATE_REJECTED", "message": {"messageId": "261400e6-4766-4e6b-b04a-484b6d276…
```

## Invalid offer: failed before any model call: `failed.sse`

```text
data: {"result": {"task": {"id": "87c81a37-9046-44df-a239-484c08807bf9", "contextId": "4f81aa72-2b5f-4d66-9f54-ea9ea5a5d2d2", "status": {"state": "TASK_STATE_SUBMITTED"}, "history": [{"messageId": "web-1", "contextId": "4f81aa72-2b5f-4d66-9…
data: {"result": {"statusUpdate": {"taskId": "87c81a37-9046-44df-a239-484c08807bf9", "contextId": "4f81aa72-2b5f-4d66-9f54-ea9ea5a5d2d2", "status": {"state": "TASK_STATE_FAILED", "message": {"messageId": "e733511c-aac8-442a-a974-56a57cfe90d…
```

## Cancelled mid-run (CancelTask sent after the first status): `canceled.sse`

```text
data: {"result": {"task": {"id": "f13851f3-c895-49c7-9ff3-6b4a2705e59d", "contextId": "203a56a5-2fbb-4c7d-9911-7956fd643550", "status": {"state": "TASK_STATE_SUBMITTED"}, "history": [{"messageId": "web-1", "contextId": "203a56a5-2fbb-4c7d-9…
data: {"result": {"statusUpdate": {"taskId": "f13851f3-c895-49c7-9ff3-6b4a2705e59d", "contextId": "203a56a5-2fbb-4c7d-9911-7956fd643550", "status": {"state": "TASK_STATE_WORKING", "message": {"messageId": "9cf460a0-e8b3-4bfc-b4cd-a5e7373fdc…
data: {"result": {"statusUpdate": {"taskId": "f13851f3-c895-49c7-9ff3-6b4a2705e59d", "contextId": "203a56a5-2fbb-4c7d-9911-7956fd643550", "status": {"state": "TASK_STATE_CANCELED", "timestamp": "2026-10-22T12:57:24.770517Z"}}}, "id": 1, "js…
```

## The CancelTask reply: `cancel-response.json`

```json
{"result":{"id":"f13851f3-c895-49c7-9ff3-6b4a2705e59d","contextId":"203a56a5-2fbb-4c7d-9911-7956fd643550","status":{"state":"TASK_STATE_CANCELED","timestamp":"2026-10-22T12:57:24.770517Z"},"history":[{"messageId":"web-1","contextId":"203a56a5-2fbb-4c7d-9911-7956fd643550","taskId":"f13851f3-c895-49c7-9ff3-6b4a2705e59d","role":"ROLE_USER","parts":[{"data":{"background":"MSc in computer science; five…
```

## A JSON-RPC error (`application/json`): `rpc-error.json`

```json
{"error":{"code":-32601,"message":"Method not found"},"id":1,"jsonrpc":"2.0"}
```

