// The salary picture for up to four codes, one row each, on one shared SEK axis (006 US3,
// research R6, contracts/ui.md "Salary chart"). Every value is read from the API's payloads; the
// page computes positions, never figures. The eye goes to the middle half of the market and the
// candidate's number; the floor is a muted gate. Marks follow the dataviz skill: bars <= 24 px,
// 2 px lines, recessive hairline axis, a legend of only the marks drawn.
import { useLayoutEffect, useRef, useState } from "react";
import type { EligibilityAnswer, Registry, SalaryPayload } from "../api/client";
import { scale } from "../lib/chartScale";
import { REGIONS, type Region } from "../lib/urlState";
import { SourceLink } from "./SourceLink";

export const CHART_WIDTH = 600; // until the figure is measured (and in tests, where nothing is)
const ROW_H = 36;
const EST_H = 12;
const BAR_H = 14;
const LABEL_H = 16;
export const sek = (n: number) => `${n.toLocaleString("sv-SE")} SEK`;
const compact = (n: number) => (n === 0 ? "0" : `${n / 1000}k`);

type Simulated = NonNullable<SalaryPayload["simulated"]>;
export type Floor = { rule: string; amount: number; percent: number | null };
export type Row = {
  code: string;
  title_en: string;
  title_sv: string;
  spread: { p10: number; p90: number } | null;
  middle: { p25: number; p75: number } | null;
  p25: number | null;
  p75: number | null;
  median: number | null;
  floor: Floor | null;
  estimate: Simulated | null;
  notes: string[];
  tables: string[];
};

/** "Estimate for ages 25-34 in Stockholm": the factors the estimate applied, in words. */
export function estimateLabel(e: Simulated) {
  return `Estimate${e.age_band ? ` for ages ${e.age_band}` : ""}${
    e.region ? ` in ${REGIONS[e.region as Region] ?? e.region}` : ""}`;
}

/** One row per payload: what to draw and what to say about it. Shared by the chart and its table. */
export function chartRows(payloads: SalaryPayload[], eligibility: Record<string, EligibilityAnswer | null>): Row[] {
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
    const tables = [...new Set([...p.distributions.slice(-1), ...(p.simulated?.inputs ?? []).map(
      (i) => ({ source_table: i.table, reference_year: i.reference_year }))].map(
      (t) => `${t.source_table} (${t.reference_year})`))];
    return {
      code: p.code,
      title_en: p.title_en,
      title_sv: p.title_sv,
      spread: d?.p10 != null && d.p90 != null ? { p10: d.p10, p90: d.p90 } : null,
      middle: d?.p25 != null && d.p75 != null ? { p25: d.p25, p75: d.p75 } : null,
      p25: d?.p25 ?? null,
      p75: d?.p75 ?? null,
      median: d?.median ?? null,
      floor,
      estimate: p.simulated ?? null,
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
export function useWidth() {
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

function RowMarks({ row, x, width, number, onShow }: { row: Row; x: (v: number) => number; width: number;
  number: number | null; onShow: (m: Mark) => void }) {
  const mid = ROW_H / 2;
  const { spread, middle, estimate: est } = row;
  const drawEst = est && est.p25 != null && est.p75 != null;
  const h = ROW_H + (drawEst ? EST_H : 0);
  return (
    <svg width={width} height={h} viewBox={`0 0 ${width} ${h}`} className="block overflow-visible">
      {row.floor && (
        <Focusable mark={{ key: "floor", text: `${row.code}: salary floor ${sek(row.floor.amount)}` }} onShow={onShow}>
          <line data-testid="floor" x1={x(row.floor.amount)} x2={x(row.floor.amount)} y1={0} y2={h}
            stroke="var(--color-muted)" strokeWidth={2} strokeDasharray="5 3" />
          <rect x={x(row.floor.amount) - 8} width={16} y={0} height={h} fill="transparent" />
        </Focusable>
      )}
      {spread && (
        <Focusable mark={{ key: "spread", text: `${row.code}: P10 ${sek(spread.p10)} to P90 ${sek(spread.p90)}` }} onShow={onShow}>
          <rect data-testid="spread" x={x(spread.p10)} width={x(spread.p90) - x(spread.p10)} y={mid - BAR_H / 2}
            height={BAR_H} rx={4} fill="var(--color-band)" />
        </Focusable>
      )}
      {middle && (
        <Focusable mark={{ key: "middle", text: `${row.code}: middle half, P25 ${sek(middle.p25)} to P75 ${sek(middle.p75)}` }} onShow={onShow}>
          <rect data-testid="middle" x={x(middle.p25)} width={x(middle.p75) - x(middle.p25)} y={mid - BAR_H / 2}
            height={BAR_H} rx={4} fill="var(--color-bar)" />
        </Focusable>
      )}
      {row.median != null && (
        <Focusable mark={{ key: "median", text: `${row.code}: median ${sek(row.median)}` }} onShow={onShow}>
          <line data-testid="median" x1={x(row.median)} x2={x(row.median)} y1={mid - 11} y2={mid + 11}
            stroke="var(--color-ink)" strokeWidth={2} strokeLinecap="round" />
          <rect x={x(row.median) - 8} width={16} y={mid - 12} height={24} fill="transparent" />
        </Focusable>
      )}
      {drawEst && (
        <Focusable mark={{ key: "estimate", text: `${row.code}: ${estimateLabel(est)}, P25 ${sek(est.p25!)} to P75 ${
          sek(est.p75!)} (not an SCB figure)` }} onShow={onShow}>
          <rect data-testid="estimate" x={x(est.p25!)} width={x(est.p75!) - x(est.p25!)} y={ROW_H - 1} height={8} rx={3}
            fill="transparent" stroke="var(--color-ink)" strokeWidth={1.5} strokeDasharray="4 3" />
        </Focusable>
      )}
      {number != null && (
        <Focusable mark={{ key: "number", text: `${row.code}: your number ${sek(number)}` }} onShow={onShow}>
          <line data-testid="number" x1={x(number)} x2={x(number)} y1={0} y2={h}
            stroke="var(--color-dot)" strokeWidth={2} />
          <rect x={x(number) - 8} width={16} y={0} height={h} fill="transparent" />
        </Focusable>
      )}
    </svg>
  );
}

/** The labels for the lines that cross every row, written once above the first row. */
function LineLabels({ x, width, number, floor }: { x: (v: number) => number; width: number;
  number: number | null; floor: number | null }) {
  if (number == null && floor == null) return null;
  return (
    <svg width={width} height={LABEL_H} viewBox={`0 0 ${width} ${LABEL_H}`} className="block overflow-visible" aria-hidden>
      {floor != null && (
        <text x={x(floor) - 4} y={12} fontSize={12} textAnchor="end" fill="var(--color-muted)">floor</text>
      )}
      {number != null && (
        <text x={x(number) + 4} y={12} fontSize={12} fontWeight={600} fill="var(--color-ink)">
          {`your ${number.toLocaleString("sv-SE")}`}
        </text>
      )}
    </svg>
  );
}

function Legend({ rows, number }: { rows: Row[]; number: number | null }) {
  const item = "flex items-center gap-1.5";
  return (
    <ul aria-label="Legend" className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
      {rows.some((r) => r.spread) && <li className={item}><svg width="18" height="10" aria-hidden><rect width="18" height="10" rx="3" fill="var(--color-band)" /></svg>P10–P90</li>}
      {rows.some((r) => r.middle) && <li className={item}><svg width="18" height="10" aria-hidden><rect width="18" height="10" rx="3" fill="var(--color-bar)" /></svg>Middle half (P25–P75)</li>}
      {rows.some((r) => r.median != null) && <li className={item}><svg width="4" height="14" aria-hidden><line x1="2" x2="2" y1="0" y2="14" stroke="var(--color-ink)" strokeWidth="2" /></svg>Median</li>}
      {rows.some((r) => r.estimate) && <li className={item}><svg width="18" height="10" aria-hidden><rect x="1" y="1" width="16" height="8" rx="3" fill="transparent" stroke="var(--color-ink)" strokeDasharray="3 2" /></svg>Estimate (not an SCB figure)</li>}
      {number != null && <li className={item}><svg width="4" height="14" aria-hidden><line x1="2" x2="2" y1="0" y2="14" stroke="var(--color-dot)" strokeWidth="2" /></svg>Your number</li>}
      {rows.some((r) => r.floor) && <li className={item}><svg width="4" height="14" aria-hidden><line x1="2" x2="2" y1="0" y2="14" stroke="var(--color-muted)" strokeWidth="2" strokeDasharray="4 2" /></svg>Salary floor</li>}
    </ul>
  );
}

function ChartTable({ rows, number }: { rows: Row[]; number: number | null }) {
  const v = (n: number | null | undefined) => (n == null ? "not published" : sek(n));
  return (
    <table aria-label="Salary by code" className="w-full text-left text-sm [&_td]:py-1 [&_td]:pr-3 [&_th]:pr-3">
      <thead className="text-xs text-muted">
        <tr><th>Code</th><th>P10</th><th>P25</th><th>Median</th><th>P75</th><th>P90</th><th>Estimate P25–P75</th>
          <th>Floor</th><th>Your number</th></tr>
      </thead>
      <tbody className="tabular-nums">
        {rows.map((r) => (
          <tr key={r.code} aria-label={`${r.code} ${r.title_en}`}>
            <td>{r.code}</td><td>{v(r.spread?.p10)}</td><td>{v(r.p25)}</td><td>{v(r.median)}</td>
            <td>{v(r.p75)}</td><td>{v(r.spread?.p90)}</td>
            <td>{r.estimate ? `${v(r.estimate.p25)} – ${v(r.estimate.p75)}` : "none"}</td>
            <td>{r.floor ? sek(r.floor.amount) : "none"}</td><td>{number != null ? sek(number) : "none"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

type Props = {
  payloads: SalaryPayload[];
  eligibility: Record<string, EligibilityAnswer | null>;
  number: number | null; // the candidate's full-time-equivalent figure, drawn across every row
  rules?: Registry["rules"]; // each floor links its rule's source (Principle III)
};

export function SalaryChart({ payloads, eligibility, number, rules }: Props) {
  const [shown, setShown] = useState<Mark | null>(null);
  const [asTable, setAsTable] = useState(false);
  const { ref, width } = useWidth();
  const rows = chartRows(payloads, eligibility);
  const { x, ticks } = scale(rows.flatMap((r) => [r.spread?.p10, r.spread?.p90, r.p25, r.p75, r.median,
    r.floor?.amount, r.estimate?.p25, r.estimate?.p75, number]), width);
  const every = width / ticks.length < 44 ? 2 : 1; // label every other tick when they would crowd
  const tables = [...new Set(rows.flatMap((r) => r.tables))];
  return (
    <figure className="space-y-3 rounded border border-line bg-panel p-3">
      <Legend rows={rows} number={number} />
      <div ref={ref} aria-hidden className="h-0" />
      {rows.map((r, i) => (
        <div key={r.code} role="group" aria-label={`${r.code} ${r.title_en}`} className="space-y-1">
          <div className="flex flex-wrap items-baseline justify-between gap-x-3 text-sm">
            <p><span className="font-mono font-semibold">{r.code}</span> {r.title_en}{" "}
              <span className="text-muted" lang="sv">{r.title_sv}</span></p>
            {r.floor && (
              <p data-floor-label className="text-xs">
                Salary floor {sek(r.floor.amount)}
                {r.floor.percent != null && ` (${r.floor.percent} % of the median)`}
                {rules?.[r.floor.rule] && <>{" · "}<SourceLink source={rules[r.floor.rule].source} /></>}
              </p>
            )}
          </div>
          {i === 0 && <LineLabels x={x} width={width} number={number} floor={r.floor?.amount ?? null} />}
          <RowMarks row={r} x={x} width={width} number={number} onShow={setShown} />
          {r.estimate && (
            <details className="text-xs text-muted">
              <summary>{estimateLabel(r.estimate)}: not an SCB figure</summary>
              <p>{r.estimate.formula}</p>
              <p>Inputs: {r.estimate.inputs.map((t) => `${t.table} (${t.reference_year})`).join(", ")}</p>
              {(r.estimate.left_out ?? []).map((lo) => <p key={lo.factor}>Not adjusted for {lo.factor === "age" ? "age" : "area"}: {lo.reason}.</p>)}
            </details>
          )}
          {r.notes.map((n) => <p key={n} className="text-xs text-warn">{n}</p>)}
        </div>
      ))}
      <svg data-testid="axis" width={width} height={16} viewBox={`0 0 ${width} 16`} className="block overflow-visible" aria-hidden>
        <line x1={0} x2={width} y1={0} y2={0} stroke="var(--color-axis)" strokeWidth={1} />
        {ticks.map((t, i) => i % every === 0 && (
          <text key={t} x={x(t)} y={13} fontSize={12} fill="var(--color-muted)"
            textAnchor={i === 0 ? "start" : i === ticks.length - 1 ? "end" : "middle"}>
            {compact(t)}
          </text>
        ))}
      </svg>
      <p role="status" className="min-h-5 text-sm">
        {shown?.text ?? (number == null ? "Enter your number to see it on the chart. Hover, tap or tab to a mark to read its value."
          : "Hover, tap or tab to a mark to read its value.")}
      </p>
      <figcaption className="text-xs text-muted">
        Monthly salary, SEK. Source: SCB {tables.join(", ")}. Medlingsinstitutet / SCB lönestrukturstatistik (AM0110).
        {rows.some((r) => r.estimate) && " Estimates are not SCB figures."}
        {" "}The floors are information, not legal advice.
      </figcaption>
      <div>
        <button type="button" className="text-sm text-accent underline" onClick={() => setAsTable(!asTable)}
          aria-expanded={asTable}>
          {asTable ? "Hide the table" : "Show as a table"}
        </button>
        <div className={asTable ? "mt-2 overflow-x-auto" : "sr-only"}>
          <ChartTable rows={rows} number={number} />
        </div>
      </div>
    </figure>
  );
}
