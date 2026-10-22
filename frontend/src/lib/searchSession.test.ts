import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { SearchAnswer } from "../api/client";
import { fixture } from "../test/fakeApi";
import { MAX_TEXT, PAUSE_MS, type SearchFn, type SessionState, SearchSession, wantsParseAd } from "./searchSession";

const FAST = fixture("search-title-fast").body as SearchAnswer;
const FULL = fixture("search-title-full").body as SearchAnswer;

type Call = { text: string; mode: string; parse_ad: boolean; signal: AbortSignal;
  resolve: (a: SearchAnswer) => void; reject: (e: unknown) => void };

function harness() {
  const calls: Call[] = [];
  const search: SearchFn = (req, signal) => new Promise((resolve, reject) =>
    calls.push({ text: req.text, mode: req.mode ?? "fast", parse_ad: !!req.parse_ad, signal, resolve, reject }));
  const states: SessionState[] = [];
  const session = new SearchSession(search, (s) => states.push(s));
  return { calls, session, last: () => states.at(-1)! };
}

const flush = () => vi.advanceTimersByTimeAsync(0);

describe("SearchSession", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("sends a fast search at once on every change, aborting the one in flight", () => {
    const { calls, session } = harness();
    session.setText("b");
    session.setText("ba");
    expect(calls.map((c) => [c.text, c.mode])).toEqual([["b", "fast"], ["ba", "fast"]]);
    expect(calls[0].signal.aborted).toBe(true);
    expect(calls[1].signal.aborted).toBe(false);
  });

  it(`sends the full search after ${PAUSE_MS} ms without a change`, async () => {
    const { calls, session } = harness();
    session.setText("backend");
    await vi.advanceTimersByTimeAsync(PAUSE_MS - 1);
    expect(calls.filter((c) => c.mode === "full")).toHaveLength(0);
    await vi.advanceTimersByTimeAsync(1);
    expect(calls.filter((c) => c.mode === "full").map((c) => c.text)).toEqual(["backend"]);
  });

  it("shows only answers for the text in the box", async () => {
    const { calls, session, last } = harness();
    session.setText("old");
    session.setText("new");
    calls[1].resolve({ ...FAST, searched_text: "new" });
    calls[0].resolve({ ...FAST, searched_text: "old" });
    await flush();
    expect(last().shown).toBe("fast");
    expect(last().answer?.searched_text).toBe("new");
    expect(last().answerFor).toBe("new");
  });

  it("replaces fast with full, and a later fast answer does not undo it", async () => {
    const { calls, session, last } = harness();
    session.setText("backend developer");
    await vi.advanceTimersByTimeAsync(PAUSE_MS);
    const [fast, full] = calls;
    full.resolve(FULL);
    await flush();
    fast.resolve(FAST);
    await flush();
    expect(last().shown).toBe("full");
    expect(last().answer).toBe(FULL);
  });

  it("shows the fast answer for new text after a full answer for older text", async () => {
    const { calls, session, last } = harness();
    session.setText("backend");
    await vi.advanceTimersByTimeAsync(PAUSE_MS);
    calls[1].resolve(FULL);
    await flush();
    session.setText("backend developer");
    calls[2].resolve(FAST);
    await flush();
    expect(last().shown).toBe("fast");
    expect(last().answer).toBe(FAST);
  });

  it("shows a fast answer for a query that was accurate before the box was cleared", async () => {  // Copilot on PR #4
    const { calls, session, last } = harness();
    session.setText("backend");
    await vi.advanceTimersByTimeAsync(PAUSE_MS);
    calls[1].resolve(FULL);
    await flush();
    session.setText("");
    session.setText("backend");
    calls[2].resolve(FAST);
    await flush();
    expect(last().answer).toBe(FAST);
  });

  it("parses a pasted ad but not a typed title", () => {
    expect(wantsParseAd("backend developer")).toBe(false);
    expect(wantsParseAd("Backend Developer\nYou will build APIs")).toBe(true);
    expect(wantsParseAd(Array(41).fill("word").join(" "))).toBe(true);
    const { calls, session } = harness();
    session.setText("Backend Developer\n\nYou will build APIs");
    expect(calls[0].parse_ad).toBe(true);
  });

  it("sends nothing for empty text and clears the list", async () => {
    const { calls, session, last } = harness();
    session.setText("backend");
    calls[0].resolve(FAST);
    await flush();
    session.setText("   ");
    await vi.advanceTimersByTimeAsync(PAUSE_MS);
    expect(calls).toHaveLength(1);
    expect(last().answer).toBeNull();
  });

  it("refuses text over the API's limit and states it", async () => {
    const { calls, session, last } = harness();
    session.setText("x".repeat(MAX_TEXT + 1));
    await vi.advanceTimersByTimeAsync(PAUSE_MS);
    expect(calls).toHaveLength(0);
    expect(last().error).toMatch(/20 000 characters/);
  });

  it("keeps the previous list and reports a failed request", async () => {
    const { calls, session, last } = harness();
    session.setText("backend");
    calls[0].resolve(FAST);
    await flush();
    session.setText("backend d");
    calls[1].reject(new Error("network down"));
    await flush();
    expect(last().answer).toBe(FAST);
    expect(last().error).toMatch(/search failed/i);
  });

  it("does not report an aborted request as an error", async () => {
    const { calls, session, last } = harness();
    session.setText("b");
    session.setText("ba");
    calls[0].reject(new DOMException("aborted", "AbortError"));
    await flush();
    expect(last().error).toBeNull();
  });
});
