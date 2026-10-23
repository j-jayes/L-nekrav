// One SEK axis for every row of the salary chart: zero baseline, linear (research R8).
const STEP = 10_000;

export function scale(values: (number | null | undefined)[], width: number) {
  const top = Math.max(0, ...values.filter((v): v is number => v != null));
  const max = Math.max(STEP, Math.ceil(top / STEP) * STEP);
  const ticks = Array.from({ length: max / STEP + 1 }, (_, i) => i * STEP);
  return { max, ticks, x: (v: number) => (v / max) * width };
}
