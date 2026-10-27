import { describe, expect, it } from "vitest";
import { scale } from "./chartScale";

describe("chart scale", () => {
  it("is padded around the drawn values instead of starting at zero (006 R6)", () => {
    const s = scale([39600, 72600, 31000, null], 500);
    expect(s.min).toBe(20000);
    expect(s.max).toBe(80000);
    expect(s.ticks).toEqual([20000, 30000, 40000, 50000, 60000, 70000, 80000]);
  });

  it("keeps every value strictly inside the axis and the axis above zero", () => {
    for (const values of [[41000, 77800], [34500, 60000, 72600], [60000], [5000, 9000]]) {
      const s = scale(values, 400);
      expect(s.min).toBeGreaterThanOrEqual(0);
      for (const v of values) {
        expect(v).toBeGreaterThan(s.min);
        expect(v).toBeLessThan(s.max);
      }
    }
  });

  it("uses 5 000 steps when the span is under 30 000", () => {
    const s = scale([41000, 55000], 400);
    expect(s.ticks[1] - s.ticks[0]).toBe(5000);
  });

  it("maps values linearly onto the width, the same for every row", () => {
    const s = scale([30000, 70000], 400);
    expect(s.x(s.min)).toBe(0);
    expect(s.x(s.max)).toBe(400);
    expect(s.x((s.min + s.max) / 2)).toBe(200);
  });

  it("keeps a usable axis when there are no values at all", () => {
    const s = scale([null, null], 300);
    expect(s.max).toBeGreaterThan(s.min);
    expect(s.x(s.max)).toBe(300);
  });
});
