import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { Offer, SalaryPayload } from "../api/client";
import cancelReply from "../test/fixtures/a2a/cancel-response.json?raw";
import completed from "../test/fixtures/a2a/completed.sse?raw";
import rejected from "../test/fixtures/a2a/rejected.sse?raw";
import { fixture } from "../test/fakeApi";
import { AdvisorDrawer } from "./AdvisorDrawer";

const card = fixture("agent-card").body as { description: string };
const salary = fixture("salary-2512").body as SalaryPayload;
const OFFER = { monthly_salary_sek: 52000, fte_percent: 100, application_type: "first_permit",
  filed_on: "2026-10-01" } as Offer;

/** The captured run with its compare event turned into a get_occupation_salary event for 2512. */
function withSalaryEvent() {
  const events = completed.split("\r\n\r\n");
  const i = events.findIndex((e) => e.includes("artifactUpdate") && e.includes("compare_occupations"));
  const d = JSON.parse(events[i].slice(5));
  d.result.artifactUpdate.artifact.name = "ui_sync:get_occupation_salary";
  d.result.artifactUpdate.artifact.parts[0].data = { kind: "ui_sync", tool: "get_occupation_salary",
    args: { code: "2512" }, result: salary };
  return [...events.slice(0, i + 1), `data: ${JSON.stringify(d)}`, ...events.slice(i + 1)].join("\r\n\r\n");
}

type Reply = { body: string; type?: string; hold?: Promise<void> };
function stubFetch(replies: Record<string, Reply[]>) {
  const calls: { url: string; body?: unknown }[] = [];
  vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
    const body = init?.body ? JSON.parse(init.body as string) : undefined;
    calls.push({ url, body });
    const key = body?.method ?? url;
    const reply = replies[key]?.shift();
    if (!reply) return new Response("{}", { status: 404 });
    const stream = new ReadableStream<Uint8Array>({
      async start(c) {
        const bytes = new TextEncoder().encode(reply.body);
        const half = bytes.indexOf(13, bytes.length / 2); // stop mid-stream until `hold` settles
        c.enqueue(bytes.slice(0, reply.hold ? half : bytes.length));
        if (reply.hold) { await reply.hold; c.enqueue(bytes.slice(half)); }
        c.close();
      },
    });
    return new Response(stream, { headers: { "Content-Type": reply.type ?? "text/event-stream" } });
  }));
  return calls;
}

function setup(replies: Record<string, Reply[]>, offer: Offer | null = OFFER) {
  const calls = stubFetch({ "/.well-known/agent-card.json": [{ body: JSON.stringify(card), type: "application/json" }], ...replies });
  const dispatch = vi.fn();
  render(<AdvisorDrawer offer={offer} dispatch={dispatch} onClose={() => {}} />);
  return { calls, dispatch };
}

async function ask(ad = "Backend developer, Python") {
  await userEvent.type(screen.getByLabelText(/job ad/i), ad);
  await userEvent.click(screen.getByRole("button", { name: /^ask/i }));
}

describe("AdvisorDrawer", () => {
  it("says the message goes to a third-party model before the first send", async () => {
    setup({});
    expect(await screen.findByText(card.description)).toBeInTheDocument();
  });

  it("shows progress, selects the codes the advisor looks up, and renders the memo", async () => {
    const { dispatch } = setup({ SendStreamingMessage: [{ body: withSalaryEvent() }] });
    await ask();
    const memo = await screen.findByRole("region", { name: /memo/i });
    expect(memo).toHaveTextContent(/third-party language model/);
    expect(memo.querySelector("script, iframe")).toBeNull();
    const progress = screen.getByRole("list", { name: /progress/i });
    expect(within(progress).getByText("Reading the job ad")).toBeInTheDocument();
    expect(dispatch).toHaveBeenCalledWith({ type: "advisor", codes: ["2512"] });
    expect(dispatch).toHaveBeenCalledWith({ type: "payload", code: "2512", payload: salary });
    expect(dispatch).toHaveBeenCalledWith({ type: "advisor", codes: ["2512", "2511"] });
  });

  it("sends the offer only when asked to", async () => {
    const { calls } = setup({ SendStreamingMessage: [{ body: rejected }, { body: rejected }] });
    await ask();
    await screen.findByText(/unavailable/i);
    const sent = (n: number) => calls.filter((c) => c.body)[n].body as { params: { message: { parts: { data: object }[] } } };
    expect(sent(0).params.message.parts[0].data).not.toHaveProperty("offer");
    await userEvent.click(screen.getByRole("checkbox", { name: /include my offer/i }));
    await userEvent.click(screen.getByRole("button", { name: /try again/i }));
    await waitFor(() => expect(sent(1).params.message.parts[0].data).toMatchObject({ offer: OFFER }));
  });

  it("explains an unavailable advisor and offers a retry", async () => {
    setup({ SendStreamingMessage: [{ body: rejected }] });
    await ask();
    expect(await screen.findByText(/Agent unavailable/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
  });

  it("refuses a second request while one runs, and can cancel it", async () => {
    let release = () => {};
    const hold = new Promise<void>((r) => { release = r; });
    const { calls } = setup({
      SendStreamingMessage: [{ body: completed, hold }],
      CancelTask: [{ body: cancelReply, type: "application/json" }],
    });
    await ask();
    await screen.findByText("Reading the job ad");
    expect(screen.getByRole("button", { name: /^ask/i })).toBeDisabled();
    expect(screen.getByText(/a request is running/i)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(await screen.findByText(/cancelled/i)).toBeInTheDocument();
    expect(calls.some((c) => (c.body as { method?: string })?.method === "CancelTask")).toBe(true);
    release();
  });
});
