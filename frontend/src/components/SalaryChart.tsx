// The salary picture for up to four codes, one row each, on one zero-based SEK axis (US2,
// research R8, contracts/ui.md "Chart marks"). Every value is read from the API's payloads; the
// page computes positions, never figures. Marks follow the dataviz skill: bars <= 24 px, 2 px
// lines, >= 8 px dots with a 2 px surface ring, recessive hairline grid.
import { useLayoutEffect, useRef, useState } from "react";
import type { EligibilityAnswer, SalaryPayload } from "../api/client";
import { scale } from "../lib/chartScale";

export const CHART_WIDTH = 600; // until the figure is measured (and in tests, where nothing is)
const ROW_H = 36;
const GHOST_H = 18;
const BAR_H = 14;
export const sek = (n: number) => `${n.toLocaleString("sv-SE")} SEK`;
const compact = (n: number) => (n === 0 ? "0" : `${n / 1000}k`);

type Simulated = NonNullable<SalaryPayload["simulated"]>;
export type Floor = { rule: string; amount: number; percent: number | null };
export type Row = {
  code: string;
  title_en: string;
  title_sv: string;
  bar: { p10: number; p90: number; p25: number | null } | null;
  median: number | null;
  ages: { band: string; mean: number }[];
  floor: Floor | null;
  simulated: Simulated | null;
  notes: string[];
  tables: string[];
};

/** One row per payload: what to draw and what to say about it. Shared by the chart and its table. */
export function chartRows(payloads: SalaryPayload[], eligibility: Record<string, EligibilityAnswer | null>,
  simulatedOn: Record<string, boolean>): Row[] {
  return payloads.map((p) => {
    const d = p.distributions.at(-1) ?? null;
    const notes: string[] = [];
    if (!d) notes.push("SCB publishes no salary figures for this code.");
    else if (d.suppressed.length)
      notes.push(`SCB does not publish ${d.suppressed.filter((f) => f !== "mean").join(", ") || "the mean"} for this code${
        d.suppressed.length >= 5 ? ": no salary bar can be drawn" : ""}.`);
    const answer = eligibility[p.code];
    let floor: Floor | null = null;
    if (answer) {
      if (answer.status !== "not_permitted" && answer.rule_id && answer.threshold_sek != null)
        floor = { rule: answer.rule_id, amount: answer.threshold_sek, percent: answer.percent ?? null };
    } else {
      const line = p.thresholds.find((t) => t.rule_id === p.applicable_rule_id);
      if (line) floor = { rule: line.rule_id, amount: line.amount_sek, percent: line.percent };
    }
    if (!floor) notes.push("Permits cannot be granted for this code, so no salary floor is drawn.");
    const tables = [...new Set([...p.distributions.slice(-1), ...p.age_bands].map(
      (t) => `${t.source_table} (${t.reference_year})`))];
    return {
      code: p.code,
      title_en: p.title_en,
      title_sv: p.title_sv,
      bar: d?.p10 != null && d.p90 != null ? { p10: d.p10, p90: d.p90, p25: d.p25 ?? null } : null,
      median: d?.median ?? null,
      ages: p.age_bands.filter((a) => a.age_band !== "all" && a.mean_monthly != null)
        .map((a) => ({ band: a.age_band, mean: a.mean_monthly! })),
      floor,
      simulated: simulatedOn[p.code] && p.simulated ? p.simulated : null,
      notes,
      tables,
    };
  });
}

type Mark = { key: string; text: string };

function Focusable({ mark, onShow, children }: { mark: Mark; onShow: (m: Mark) => void; children: React.ReactNode }) {
  const show = () => onShow(mark);
  return (
    <g tabIndex={0} role="img" aria-label={mark.text} onFocus={show} onMouseEnter={show} onClick={show}
      className="cursor-default outline-none focus-visible:[&>*]:stroke-[var(--color-ink)]">
      {children}
    </g>
  );
}

/** The figure's drawing width in CSS pixels, so marks and text keep their size on a phone. */
function useWidth() {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(CHART_WIDTH);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(([e]) => e.contentRect.width && setWidth(Math.round(e.contentRect.width)));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return { ref, width };
}

function RowMarks({ row, x, width, onShow }: { row: Row; x: (v: number) => number; width: number;
  onShow: (m: Mark) => void }) {
  const mid = ROW_H / 2;
  const h = ROW_H + (row.simulated ? GHOST_H : 0);
  const { bar, simulated: sim } = row;
  return (
    <svg width={width} height={h} viewBox={`0 0 ${width} ${h}`} className="block overflow-visible">
      {bar && (
        <Focusable mark={{ key: "bar", text: `${row.code}: P10 ${sek(bar.p10)} to P90 ${sek(bar.p90)}` }} onShow={onShow}>
          <rect data-testid="bar" x={x(bar.p10)} width={x(bar.p90) - x(bar.p10)} y={mid - BAR_H / 2} height={BAR_H}
            rx={4} fill="var(--color-bar)" />
          {bar.p25 != null && (
            <rect data-testid="band" x={x(bar.p10)} width={x(bar.p25) - x(bar.p10)} y={mid - BAR_H / 2}
              height={BAR_H} rx={4} fill="var(--color-band)" />
          )}
        </Focusable>
      )}
      {row.median != null && (
        <Focusable mark={{ key: "median", text: `${row.code}: median ${sek(row.median)}` }} onShow={onShow}>
          <line data-testid="median" x1={x(row.median)} x2={x(row.median)} y1={mid - 11} y2={mid + 11}
            stroke="var(--color-ink)" strokeWidth={2} strokeLinecap="round" />
          <rect x={x(row.median) - 8} width={16} y={mid - 12} height={24} fill="transparent" />
        </Focusable>
      )}
      {row.ages.map((a) => (
        <Focusable key={a.band} mark={{ key: `age-${a.band}`, text: `${row.code}: mean ${sek(a.mean)}, ages ${a.band}` }} onShow={onShow}>
          <circle data-testid="age-dot" cx={x(a.mean)} cy={mid} r={4.5} fill="var(--color-dot)"
            stroke="var(--color-page)" strokeWidth={2} />
          <circle cx={x(a.mean)} cy={mid} r={12} fill="transparent" />
        </Focusable>
      ))}
      {row.floor && (
        <Focusable mark={{ key: "floor", text: `${row.code}: salary floor ${sek(row.floor.amount)}` }} onShow={onShow}>
          <line data-testid="floor" x1={x(row.floor.amount)} x2={x(row.floor.amount)} y1={0} y2={h}
            stroke="var(--color-ink)" strokeWidth={2} strokeDasharray="5 3" />
          <rect x={x(row.floor.amount) - 8} width={16} y={0} height={h} fill="transparent" />
        </Focusable>
      )}
      {sim && sim.p10 != null && sim.p90 != null && (
        <Focusable mark={{ key: "sim", text: `${row.code}: simulated, ages ${sim.age_band}: P10 ${sek(sim.p10)} to P90 ${sek(sim.p90)}` }} onShow={onShow}>
          <rect data-testid="simulated" x={x(sim.p10)} width={x(sim.p90) - x(sim.p10)} y={ROW_H + 2} height={10} rx={4}
            fill="var(--color-bar)" fillOpacity={0.1} stroke="var(--color-bar)" strokeWidth={1.5} strokeDasharray="4 3" />
        </Focusable>
      )}
    </svg>
  );
}

function Legend() {
  const item = "flex items-center gap-1.5";
  return (
    <ul aria-label="Legend" className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
      <li className={item}><svg width="18" height="10" aria-hidden><rect width="18" height="10" rx="3" fill="var(--color-band)" /></svg>P10–P25 (low-pay band)</li>
      <li className={item}><svg width="18" height="10" aria-hidden><rect width="18" height="10" rx="3" fill="var(--color-bar)" /></svg>P25–P90</li>
      <li className={item}><svg width="4" height="14" aria-hidden><line x1="2" x2="2" y1="0" y2="14" stroke="var(--color-ink)" strokeWidth="2" /></svg>Median</li>
      <li className={item}><svg width="10" height="10" aria-hidden><circle cx="5" cy="5" r="4" fill="var(--color-dot)" /></svg>Mean by age band</li>
      <li className={item}><svg width="4" height="14" aria-hidden><line x1="2" x2="2" y1="0" y2="14" stroke="var(--color-ink)" strokeWidth="2" strokeDasharray="4 2" /></svg>Salary floor</li>
      <li className={item}><svg width="18" height="10" aria-hidden><rect x="1" y="1" width="16" height="8" rx="3" fill="var(--color-bar)" fillOpacity="0.1" stroke="var(--color-bar)" strokeDasharray="3 2" /></svg>Simulated (age-adjusted, not SCB)</li>
    </ul>
  );
}

function ChartTable({ rows }: { rows: Row[] }) {
  const v = (n: number | null | undefined) => (n == null ? "not published" : sek(n));
  return (
    <table aria-label="Salary by code" className="w-full text-left text-sm [&_td]:py-1 [&_td]:pr-3 [&_th]:pr-3">
      <thead className="text-xs text-muted">
        <tr><th>Code</th><th>P10</th><th>P25</th><th>Median</th><th>P90</th><th>Floor</th></tr>
      </thead>
      <tbody className="tabular-nums">
        {rows.map((r) => (
          <tr key={r.code} aria-label={`${r.code} ${r.title_en}`}>
            <td>{r.code}</td><td>{v(r.bar?.p10)}</td><td>{v(r.bar?.p25)}</td><td>{v(r.median)}</td>
            <td>{v(r.bar?.p90)}</td><td>{r.floor ? sek(r.floor.amount) : "none"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

type Props = {
  payloads: SalaryPayload[];
  eligibility: Record<string, EligibilityAnswer | null>;
  simulated: Record<string, boolean>;
};

export function SalaryChart({ payloads, eligibility, simulated }: Props) {
  const [shown, setShown] = useState<Mark | null>(null);
  const [asTable, setAsTable] = useState(false);
  const { ref, width } = useWidth();
  const rows = chartRows(payloads, eligibility, simulated);
  const { x, ticks } = scale(rows.flatMap((r) => [r.bar?.p90, r.median, r.floor?.amount, r.simulated?.p90,
    ...r.ages.map((a) => a.mean)]), width);
  const every = width / ticks.length < 44 ? 2 : 1; // label every other tick when they would crowd
  const tables = [...new Set(rows.flatMap((r) => r.tables))];
  return (
    <figure className="space-y-3 rounded border border-line bg-panel p-3">
      <Legend />
      <div ref={ref} aria-hidden className="h-0" />
      {rows.map((r) => (
        <div key={r.code} role="group" aria-label={`${r.code} ${r.title_en}`} className="space-y-1">
          <div className="flex flex-wrap items-baseline justify-between gap-x-3 text-sm">
            <p><span className="font-mono font-semibold">{r.code}</span> {r.title_en}{" "}
              <span className="text-muted" lang="sv">{r.title_sv}</span></p>
            {r.floor && (
              <p data-floor-label className="text-xs">
                Salary floor {sek(r.floor.amount)}
                {r.floor.percent != null && ` (${r.floor.percent} % of the median)`}
              </p>
            )}
          </div>
          <RowMarks row={r} x={x} width={width} onShow={setShown} />
          {r.simulated && (
            <details className="text-xs text-muted">
              <summary>Simulated, ages {r.simulated.age_band}: not an SCB figure</summary>
              <p>{r.simulated.formula}</p>
              <p>Inputs: {r.simulated.inputs.map((i) => `${i.table} (${i.reference_year})`).join(", ")}</p>
            </details>
          )}
          {r.notes.map((n) => <p key={n} className="text-xs text-warn">{n}</p>)}
        </div>
      ))}
      <svg width={width} height={16} viewBox={`0 0 ${width} 16`} className="block overflow-visible" aria-hidden>
        <line x1={0} x2={width} y1={0} y2={0} stroke="var(--color-axis)" strokeWidth={1} />
        {ticks.map((t, i) => i % every === 0 && (
          <text key={t} x={x(t)} y={13} fontSize={12} fill="var(--color-muted)"
            textAnchor={i === 0 ? "start" : i === ticks.length - 1 ? "end" : "middle"}>
            {compact(t)}
          </text>
        ))}
      </svg>
      <p role="status" className="min-h-5 text-sm">{shown?.text ?? "Hover, tap or tab to a mark to read its value."}</p>
      <figcaption className="text-xs text-muted">
        Monthly salary, SEK. Source: SCB {tables.join(", ")}. Medlingsinstitutet / SCB lönestrukturstatistik (AM0110).
      </figcaption>
      <div>
        <button type="button" className="text-sm text-accent underline" onClick={() => setAsTable(!asTable)}
          aria-expanded={asTable}>
          {asTable ? "Hide the table" : "Show as a table"}
        </button>
        <div className={asTable ? "mt-2 overflow-x-auto" : "sr-only"}>
          <ChartTable rows={rows} />
        </div>
      </div>
    </figure>
  );
}
