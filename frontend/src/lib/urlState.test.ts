import { describe, expect, it } from "vitest";
import { parse, serialise } from "./urlState";

describe("urlState", () => {
  it("round-trips view, codes, age and area", () => {
    const s = { view: "number" as const, codes: ["2512", "2514"], age: "25-34" as const, region: "SE11" as const };
    expect(parse(serialise(s)).state).toEqual(s);
    expect(serialise(s)).toBe("?view=number&codes=2512%2C2514&age=25-34&region=SE11");
  });

  it("defaults to the search view with nothing selected", () => {
    expect(parse("").state).toEqual({ view: "search", codes: [], age: null, region: null });
    expect(serialise({ view: "search", codes: [], age: null, region: null })).toBe("?view=search");
  });

  it("opens an old compare link on Your number (006 FR-017)", () => {
    expect(parse("?view=compare&codes=2512,2511").state).toMatchObject({ view: "number", codes: ["2512", "2511"] });
  });

  it("falls back to search for an unknown view", () => {
    expect(parse("?view=admin").state.view).toBe("search");
  });

  it("drops duplicates, malformed codes and codes past the limit, and says which", () => {
    const { state, dropped } = parse("?codes=2512,2512,abcd,2514,3511,9210,5343");
    expect(state.codes).toEqual(["2512", "2514", "3511", "9210"]);
    expect(dropped).toEqual(["2512", "abcd", "5343"]);
  });

  it("ignores an unknown age band or area", () => {
    expect(parse("?age=99-100").state.age).toBeNull();
    expect(parse("?region=SE99").state.region).toBeNull();
    expect(parse("?region=SE").state.region).toBeNull(); // Sweden is the reference, not a choice
  });

  it("never writes any other key: the candidate's number stays out of the address (FR-018)", () => {
    const q = serialise({ view: "legal", codes: ["2512"], age: null, region: null, number: 60000 } as never);
    expect([...new URLSearchParams(q).keys()]).toEqual(["view", "codes"]);
    expect(q).not.toContain("60000");
  });
});
