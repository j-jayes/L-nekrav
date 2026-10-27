// The occupation map's geometry (007 research R6): positions in [0, 1] from the map artefact,
// drawn inside a padded box with y up, and a zoom/pan view (k, tx, ty) applied after projecting.
export type View = { k: number; tx: number; ty: number };
export const IDENTITY: View = { k: 1, tx: 0, ty: 0 };
const MIN_K = 1;
const MAX_K = 8;

export function project(p: { x: number; y: number }, v: View, w: number, h: number, pad: number) {
  const bx = pad + p.x * (w - 2 * pad);
  const by = h - pad - p.y * (h - 2 * pad);
  return { px: bx * v.k + v.tx, py: by * v.k + v.ty };
}

/** Zoom by `factor` about the screen point (cx, cy), which stays where it is. */
export function zoomAt(v: View, factor: number, cx: number, cy: number): View {
  const k = Math.min(MAX_K, Math.max(MIN_K, v.k * factor));
  const f = k / v.k;
  return { k, tx: cx - (cx - v.tx) * f, ty: cy - (cy - v.ty) * f };
}

export function pan(v: View, dx: number, dy: number): View {
  return { ...v, tx: v.tx + dx, ty: v.ty + dy };
}

/** Every code at the spot nearest (mx, my), if it is within `radius` pixels: points drawn on the
 * same spot come back together. A linear scan: 429 points is nothing. */
export function nearest<P extends { code: string; x: number; y: number }>(points: P[], v: View, w: number,
  h: number, pad: number, mx: number, my: number, radius: number): string[] {
  let best = Infinity;
  const d = points.map((p) => {
    const { px, py } = project(p, v, w, h, pad);
    const dist = Math.hypot(px - mx, py - my);
    best = Math.min(best, dist);
    return dist;
  });
  if (best > radius) return [];
  return points.filter((_, i) => d[i] - best < 0.5).map((p) => p.code);
}

/** The view that frames `points` inside the drawing with `margin` pixels to spare, at most 8×. */
export function fit(points: { x: number; y: number }[], w: number, h: number, pad: number, margin: number): View {
  if (!points.length) return IDENTITY;
  const base = points.map((p) => project(p, IDENTITY, w, h, pad));
  const xs = base.map((p) => p.px);
  const ys = base.map((p) => p.py);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const k = Math.min(MAX_K, Math.max(MIN_K, Math.min((w - 2 * margin) / Math.max(x1 - x0, 1),
    (h - 2 * margin) / Math.max(y1 - y0, 1))));
  return { k, tx: w / 2 - ((x0 + x1) / 2) * k, ty: h / 2 - ((y0 + y1) / 2) * k };
}
