import { describe, expect, it } from "vitest";
import { parse, serialise } from "./urlState";

describe("urlState", () => {
  it("round-trips view, codes and age", () => {
    const s = { view: "compare" as const, codes: ["2512", "2514"], age: "25-34" as const };
    expect(parse(serialise(s)).state).toEqual(s);
    expect(serialise(s)).toBe("?view=compare&codes=2512%2C2514&age=25-34");
  });

  it("defaults to the search view with nothing selected", () => {
    expect(parse("").state).toEqual({ view: "search", codes: [], age: null });
    expect(serialise({ view: "search", codes: [], age: null })).toBe("?view=search");
  });

  it("falls back to search for an unknown view", () => {
    expect(parse("?view=admin").state.view).toBe("search");
  });

  it("drops duplicates, malformed codes and codes past the limit, and says which", () => {
    const { state, dropped } = parse("?codes=2512,2512,abcd,2514,3511,9210,5343");
    expect(state.codes).toEqual(["2512", "2514", "3511", "9210"]);
    expect(dropped).toEqual(["2512", "abcd", "5343"]);
  });

  it("ignores an unknown age band", () => {
    expect(parse("?age=99-100").state.age).toBeNull();
  });

  it("never writes any other key", () => {
    const q = serialise({ view: "legal", codes: ["2512"], age: null });
    expect([...new URLSearchParams(q).keys()]).toEqual(["view", "codes"]);
  });
});
