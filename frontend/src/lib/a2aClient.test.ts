import { describe, expect, it, vi } from "vitest";
import cancelReply from "../test/fixtures/a2a/cancel-response.json?raw";
import canceled from "../test/fixtures/a2a/canceled.sse?raw";
import completed from "../test/fixtures/a2a/completed.sse?raw";
import failed from "../test/fixtures/a2a/failed.sse?raw";
import rejected from "../test/fixtures/a2a/rejected.sse?raw";
import rpcError from "../test/fixtures/a2a/rpc-error.json?raw";
import { type AdvisorEvent, cancelTask, sendMessage } from "./a2aClient";

/** A Response whose body arrives in small chunks, splitting events, CRLFs and UTF-8 sequences. */
function streamed(text: string, size = 7, type = "text/event-stream") {
  const bytes = new TextEncoder().encode(text);
  const body = new ReadableStream<Uint8Array>({
    start(c) {
      for (let i = 0; i < bytes.length; i += size) c.enqueue(bytes.slice(i, i + size));
      c.close();
    },
  });
  return new Response(body, { status: 200, headers: { "Content-Type": type } });
}

async function collect(response: Response, input = { ad: "Backend developer" }) {
  const fetchFn = vi.fn(async () => response);
  const events: AdvisorEvent[] = [];
  for await (const e of sendMessage(input, { fetchFn })) events.push(e);
  return { events, fetchFn };
}

describe("a2aClient", () => {
  it("reads a full run as task, progress, ui_sync, memo and a final state", async () => {
    const { events } = await collect(streamed(completed));
    expect(events.map((e) => e.type === "status" ? `status:${e.state}` : e.type)).toEqual([
      "task", "status:working", "status:working", "ui_sync", "status:working", "ui_sync", "memo", "status:completed"]);
    const sync = events.filter((e) => e.type === "ui_sync");
    expect(sync.map((e) => e.type === "ui_sync" && e.tool)).toEqual(["search_occupations", "compare_occupations"]);
    const memo = events.find((e) => e.type === "memo");
    expect(memo?.type === "memo" && memo.markdown).toMatch(/third-party language model/);
    expect(events[1]).toMatchObject({ type: "status", text: "Reading the job ad" });
  });

  it("gives the reason when the server has no key", async () => {
    const { events } = await collect(streamed(rejected));
    expect(events.at(-1)).toMatchObject({ type: "status", state: "rejected", text: expect.stringMatching(/Agent unavailable/) });
  });

  it("gives the reason when the input is invalid", async () => {
    const { events } = await collect(streamed(failed));
    expect(events.at(-1)).toMatchObject({ type: "status", state: "failed", text: expect.stringMatching(/fte_percent/) });
  });

  it("ends canceled when the task is cancelled", async () => {
    const { events } = await collect(streamed(canceled));
    expect(events.at(-1)).toMatchObject({ type: "status", state: "canceled" });
  });

  it("turns a JSON-RPC error into a failed event", async () => {
    const { events } = await collect(streamed(rpcError, 7, "application/json"));
    expect(events).toEqual([{ type: "error", state: "failed", message: "Method not found" }]);
  });

  it("reports a stream that stops before a final state as lost", async () => {
    const cut = completed.slice(0, completed.indexOf("ui_sync:compare_occupations"));
    const { events } = await collect(streamed(cut.slice(0, cut.lastIndexOf("\r\n\r\n") + 4)));
    expect(events.at(-1)).toEqual({ type: "error", state: "lost", message: expect.stringMatching(/connection/i) });
  });

  it("sends one data part with the A2A v1.0 headers", async () => {
    const { fetchFn } = await collect(streamed(rejected), { ad: "Backend developer", background: "MSc" } as never);
    const [url, init] = fetchFn.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/a2a");
    expect(init.headers).toMatchObject({ "A2A-Version": "1.0", Accept: "text/event-stream" });
    const body = JSON.parse(init.body as string);
    expect(body.method).toBe("SendStreamingMessage");
    expect(body.params.message.parts).toEqual([{ data: { ad: "Backend developer", background: "MSc" } }]);
  });

  it("cancels a task by id", async () => {
    const fetchFn = vi.fn(async () => new Response(cancelReply, { headers: { "Content-Type": "application/json" } }));
    expect(await cancelTask("t-1", { fetchFn })).toBe("canceled");
    const body = JSON.parse((fetchFn.mock.calls[0] as unknown as [string, RequestInit])[1].body as string);
    expect(body).toMatchObject({ method: "CancelTask", params: { id: "t-1" } });
  });
});
