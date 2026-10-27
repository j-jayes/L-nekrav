// One SEK axis for every row of the salary chart, padded around the values drawn rather than
// starting at zero (006 research R6): the eye goes to the market, not to empty space.
const STEP = 10_000;
const FINE = 5_000; // under a 30 000 span, 10 000 steps leave too few ticks

export function scale(values: (number | null | undefined)[], width: number) {
  const drawn = values.filter((v): v is number => v != null);
  if (!drawn.length) return { min: 0, max: STEP, ticks: [0, STEP], x: (v: number) => (v / STEP) * width };
  const lo = Math.min(...drawn);
  const hi = Math.max(...drawn);
  const step = hi - lo < 30_000 ? FINE : STEP;
  const min = Math.max(0, Math.floor((lo - step / 2) / step) * step);
  const max = Math.ceil((hi + step / 2) / step) * step;
  const ticks = Array.from({ length: (max - min) / step + 1 }, (_, i) => min + i * step);
  return { min, max, ticks, x: (v: number) => ((v - min) / (max - min)) * width };
}
