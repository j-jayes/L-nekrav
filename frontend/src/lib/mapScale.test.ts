import { describe, expect, it } from "vitest";
import { IDENTITY, nearest, project, zoomAt } from "./mapScale";

const pts = [
  { code: "1311", x: 0.2, y: 0.2 },
  { code: "1312", x: 0.2, y: 0.2 }, // drawn on the same spot
  { code: "2512", x: 0.85, y: 0.6 },
];

describe("map scale", () => {
  it("projects [0, 1] positions inside the padded drawing, y up", () => {
    const p = project({ x: 0, y: 0 }, IDENTITY, 400, 300, 20);
    expect(p).toEqual({ px: 20, py: 280 });
    expect(project({ x: 1, y: 1 }, IDENTITY, 400, 300, 20)).toEqual({ px: 380, py: 20 });
  });

  it("zooms about the pointer, so the point under it stays put", () => {
    const before = project(pts[2], IDENTITY, 400, 300, 20);
    const v = zoomAt(IDENTITY, 2, before.px, before.py);
    const after = project(pts[2], v, 400, 300, 20);
    expect(after.px).toBeCloseTo(before.px);
    expect(after.py).toBeCloseTo(before.py);
    expect(v.k).toBe(2);
  });

  it("keeps the zoom between 1× and 8×", () => {
    expect(zoomAt(IDENTITY, 0.1, 0, 0).k).toBe(1);
    expect(zoomAt({ k: 6, tx: 0, ty: 0 }, 4, 0, 0).k).toBe(8);
  });

  it("finds every code at the nearest spot within the radius", () => {
    const p = project(pts[0], IDENTITY, 400, 300, 20);
    expect(nearest(pts, IDENTITY, 400, 300, 20, p.px + 3, p.py, 12)).toEqual(["1311", "1312"]);
    expect(nearest(pts, IDENTITY, 400, 300, 20, 0, 0, 12)).toEqual([]);
  });
});

describe("fit", () => {
  it("frames the given points with a margin, never past 8×", async () => {
    const { fit } = await import("./mapScale");
    const near = [{ x: 0.5, y: 0.5 }, { x: 0.55, y: 0.52 }];
    const v = fit(near, 400, 300, 20, 40);
    for (const p of near) {
      const { px, py } = project(p, v, 400, 300, 20);
      expect(px).toBeGreaterThanOrEqual(40 - 1e-9);
      expect(px).toBeLessThanOrEqual(360 + 1e-9);
      expect(py).toBeGreaterThanOrEqual(40 - 1e-9);
      expect(py).toBeLessThanOrEqual(260 + 1e-9);
    }
    expect(v.k).toBeLessThanOrEqual(8);
    expect(fit([], 400, 300, 20, 40)).toEqual(IDENTITY);
  });
});
