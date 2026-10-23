// The browser's A2A v1.0 client for lonekrav-advisor (contracts/a2a-client.md, research R7).
// A2A streaming is a POST, so EventSource cannot be used: the response body is read as a stream
// and split into SSE events here. The wire format is captured in references/a2a-sse-wire.md.
import type { Offer } from "../api/client";

export type AdvisorInput = { ad: string; background?: string; offer?: Offer };
export type RunState = "submitted" | "working" | "completed" | "failed" | "rejected" | "canceled";
export type AdvisorEvent =
  | { type: "task"; taskId: string }
  | { type: "status"; state: RunState; text: string }
  | { type: "ui_sync"; tool: string; args: Record<string, unknown>; result: unknown }
  | { type: "memo"; markdown: string }
  | { type: "error"; state: "failed" | "lost"; message: string };

export const FINAL: RunState[] = ["completed", "failed", "rejected", "canceled"];
type Options = { fetchFn?: typeof fetch; signal?: AbortSignal };
type Part = { text?: string; data?: Record<string, unknown> };

const HEADERS = { "Content-Type": "application/json", "A2A-Version": "1.0" };
const state = (s: string) => s.replace("TASK_STATE_", "").toLowerCase() as RunState;
const text = (parts: Part[] = []) => parts.map((p) => p.text ?? "").join(" ").trim();

function rpc(method: string, params: unknown) {
  return JSON.stringify({ jsonrpc: "2.0", id: crypto.randomUUID(), method, params });
}

/** One JSON-RPC result as page events. */
function* toEvents(result: Record<string, any>): Generator<AdvisorEvent> {
  if (result.task) {
    yield { type: "task", taskId: result.task.id };
  } else if (result.statusUpdate) {
    const s = result.statusUpdate.status;
    yield { type: "status", state: state(s.state), text: text(s.message?.parts) };
  } else if (result.artifactUpdate) {
    const a = result.artifactUpdate.artifact;
    if (a.name?.startsWith("ui_sync:")) {
      const d = (a.parts as Part[])[0].data as { tool: string; args: Record<string, unknown>; result: unknown };
      yield { type: "ui_sync", tool: d.tool, args: d.args, result: d.result };
    } else if (a.name === "memo") {
      yield { type: "memo", markdown: text(a.parts) };
    }
  }
}

/** The `data:` payload of each SSE event in a byte stream. Events end at a blank line (CRLF or LF). */
async function* sseData(body: ReadableStream<Uint8Array>): AsyncGenerator<string> {
  const reader = body.getReader();
  const decoder = new TextDecoder(); // stream mode keeps a UTF-8 character split across chunks whole
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) return;
    buffer = (buffer + decoder.decode(value, { stream: true })).replace(/\r\n/g, "\n");
    let end: number;
    while ((end = buffer.indexOf("\n\n")) >= 0) {
      const event = buffer.slice(0, end);
      buffer = buffer.slice(end + 2);
      const data = event.split("\n").filter((l) => l.startsWith("data:")).map((l) => l.slice(5).trimStart());
      if (data.length) yield data.join("\n");
    }
  }
}

/** Send one request to the advisor and yield its events until the task reaches a final state. */
export async function* sendMessage(input: AdvisorInput, { fetchFn = fetch, signal }: Options = {}):
  AsyncGenerator<AdvisorEvent> {
  const message = { messageId: crypto.randomUUID(), role: "ROLE_USER", parts: [{ data: input }] };
  let response: Response;
  try {
    response = await fetchFn("/a2a", { method: "POST", signal, body: rpc("SendStreamingMessage", { message }),
      headers: { ...HEADERS, Accept: "text/event-stream" } });
  } catch (e) {
    if (signal?.aborted) return;
    yield { type: "error", state: "lost", message: `Could not reach the advisor (${(e as Error).message}).` };
    return;
  }
  if (!response.ok || !response.body) {
    yield { type: "error", state: "failed", message: `The advisor answered HTTP ${response.status}.` };
    return;
  }
  if (!response.headers.get("Content-Type")?.startsWith("text/event-stream")) {
    const reply = await response.json(); // a JSON-RPC error arrives as plain JSON, not SSE
    yield { type: "error", state: "failed", message: reply.error?.message ?? "The advisor sent no events." };
    return;
  }
  try {
    for await (const data of sseData(response.body)) {
      const reply = JSON.parse(data);
      if (reply.error) {
        yield { type: "error", state: "failed", message: reply.error.message };
        return;
      }
      for (const e of toEvents(reply.result)) {
        yield e;
        if (e.type === "status" && FINAL.includes(e.state)) return;
      }
    }
  } catch (e) {
    if (signal?.aborted) return;
    yield { type: "error", state: "lost", message: `The connection to the advisor broke (${(e as Error).message}).` };
    return;
  }
  if (!signal?.aborted)
    yield { type: "error", state: "lost", message: "The connection to the advisor closed before the run finished." };
}

/** Ask the server to cancel a task; returns the state it reports. */
export async function cancelTask(taskId: string, { fetchFn = fetch }: Options = {}): Promise<RunState | null> {
  const r = await fetchFn("/a2a", { method: "POST", headers: HEADERS, body: rpc("CancelTask", { id: taskId }) });
  const reply = await r.json();
  return reply.result?.status?.state ? state(reply.result.status.state) : null;
}

/** The agent card: whether the advisor is offered, and its description (with the third-party notice). */
export async function agentCard(fetchFn: typeof fetch = fetch) {
  const r = await fetchFn("/.well-known/agent-card.json");
  return r.ok ? ((await r.json()) as { name: string; description: string }) : null;
}
