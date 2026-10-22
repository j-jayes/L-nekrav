import { describe, expect, it } from "vitest";
import { scale } from "./chartScale";

describe("chart scale", () => {
  it("starts at zero and ends at the largest value rounded up to the next 10 000", () => {
    const s = scale([39600, 72600, 34470, null], 500);
    expect(s.max).toBe(80000);
    expect(s.ticks).toEqual([0, 10000, 20000, 30000, 40000, 50000, 60000, 70000, 80000]);
  });

  it("maps values linearly onto the width, the same for every row", () => {
    const s = scale([50000], 400);
    expect(s.x(0)).toBe(0);
    expect(s.x(25000)).toBe(200);
    expect(s.x(50000)).toBe(400);
  });

  it("keeps a usable axis when there are no values at all", () => {
    const s = scale([null, null], 300);
    expect(s.max).toBe(10000);
    expect(s.x(10000)).toBe(300);
  });

  it("does not round up a value already on a round number", () => {
    expect(scale([60000], 100).max).toBe(60000);
  });
});
