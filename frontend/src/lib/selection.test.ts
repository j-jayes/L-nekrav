import { describe, expect, it } from "vitest";
import salary2512 from "../test/fixtures/salary-2512.json";
import { initial, select, type Selection } from "./selection";

const run = (...actions: Parameters<typeof select>[1][]) =>
  actions.reduce<Selection>((s, a) => select(s, a), initial());

describe("selection", () => {
  it("adds and removes codes in order", () => {
    const s = run({ type: "add", code: "2512" }, { type: "add", code: "2514" },
      { type: "add", code: "3511" }, { type: "remove", code: "2514" });
    expect(s.codes).toEqual(["2512", "3511"]);
    expect(s.note).toBeNull();
  });

  it("does nothing for a duplicate and says so", () => {
    const s = run({ type: "add", code: "2512" }, { type: "add", code: "2512" });
    expect(s.codes).toEqual(["2512"]);
    expect(s.note).toMatch(/2512 is already selected/);
  });

  it("refuses a fifth code and asks to remove one", () => {
    const s = run(...["2512", "2514", "3511", "9210", "5343"].map((code) => ({ type: "add" as const, code })));
    expect(s.codes).toEqual(["2512", "2514", "3511", "9210"]);
    expect(s.note).toMatch(/at most four.*remove one/i);
  });

  it("keeps the four most recent codes when the advisor selects, and lists those left out", () => {
    const s = run(...["1211", "2514", "3511"].map((code) => ({ type: "add" as const, code })),
      { type: "advisor", codes: ["2512", "2511"] });
    expect(s.codes).toEqual(["2514", "3511", "2512", "2511"]);
    expect(s.leftOut).toEqual(["1211"]);
  });

  it("lets the most recent change win, whichever side made it", () => {
    let s = run({ type: "advisor", codes: ["2512", "2511"] }, { type: "remove", code: "2511" });
    expect(s.codes).toEqual(["2512"]);
    s = select(s, { type: "advisor", codes: ["2511"] });
    expect(s.codes).toEqual(["2512", "2511"]);
  });

  it("stores a payload per code and drops it with the code", () => {
    let s = run({ type: "add", code: "2512" },
      { type: "payload", code: "2512", payload: salary2512.body as never });
    expect(s.payloads["2512"]?.code).toBe("2512");
    s = select(s, { type: "remove", code: "2512" });
    expect(s.payloads["2512"]).toBeUndefined();
  });

  it("holds no per-code simulated switch: the estimate follows the age band and area (006 FR-014)", () => {
    expect(Object.keys(run({ type: "add", code: "2512" }))).not.toContain("simulated");
  });

  it("takes codes from the address with its dropped-code note", () => {
    const s = run({ type: "load", codes: ["2512"], dropped: ["abcd"] });
    expect(s.codes).toEqual(["2512"]);
    expect(s.note).toMatch(/abcd/);
  });
});
