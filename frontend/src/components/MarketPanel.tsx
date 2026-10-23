import { useEffect, useState } from "react";
import { api, type MarketAnswer, type YearlyAds } from "../api/client";
import { Notice } from "./Notice";
import { sek, useWidth } from "./SalaryChart";

const TOP = 5;
const n = (v: number) => v.toLocaleString("sv-SE");
const utc = (iso: string) => `${new Date(iso).toISOString().slice(0, 16).replace("T", " ")} UTC`;
const NO_CONCEPT = "JobTech publishes no ads under this code, so there is no count.";

/** "fetched X", or "fetched X to Y" when the figures were fetched at different times. */
function fetched(times: string[]) {
  const sorted = [...times].sort();
  const [first, last] = [utc(sorted[0]), utc(sorted.at(-1)!)];
  return first === last ? `fetched ${first}` : `fetched ${first} to ${last}`;
}

/** Codes JobTech merges share one concept, so both its live and its yearly counts. */
function Shared({ a }: { a: MarketAnswer }) {
  return a.shared_with.length > 0
    ? <p className="text-muted">Shared with {a.shared_with.join(", ")}: JobTech counts these codes together.</p>
    : null;
}

function OpenNow({ a }: { a: MarketAnswer }) {
  const l = a.live;
  let body;
  if (l.status === "no_concept") body = <p>{NO_CONCEPT}</p>;
  else if (l.status === "unavailable") body = <p>The live count is unavailable ({l.reason}).</p>;
  else {
    const [top, rest] = [l.counties.slice(0, TOP), l.counties.slice(TOP)];
    const item = (c: (typeof l.counties)[number]) => <li key={c.code} lang="sv">{c.name}: {n(c.ads)}</li>;
    body = (
      <>
        <p><strong>{n(l.ads!)} open ads</strong>, {n(l.positions!)} positions on Platsbanken</p>
        <Shared a={a} />
        <ul aria-label="Top counties" className="space-y-0.5">{top.map(item)}</ul>
        {rest.length > 0 && (
          <details>
            <summary className="cursor-pointer text-muted">{rest.length} more counties</summary>
            <ul className="mt-1 space-y-0.5">{rest.map(item)}</ul>
          </details>
        )}
        {l.no_county! > 0 && <p className="text-muted">No county given: {n(l.no_county!)}</p>}
        <p className="text-xs text-muted">
          <a className="text-accent underline" href={l.source!.url} target="_blank" rel="noreferrer">
            Arbetsförmedlingen JobSearch
          </a>, fetched {utc(l.fetched_at!)}
        </p>
      </>
    );
  }
  return (
    <section aria-label="Open now" className="space-y-1">
      <h5 className="text-xs font-semibold uppercase text-muted">Open now</h5>
      {body}
    </section>
  );
}

function PayByArea({ a, floor }: { a: MarketAnswer; floor: number | null }) {
  const label = `Pay by area${a.regional_year ? ` (${a.regional_year})` : ""}`;
  const np = <span className="text-muted">not published</span>;
  return (
    <section aria-label={label} className="space-y-1">
      <h5 className="text-xs font-semibold uppercase text-muted">{label}</h5>
      <p className="text-muted">
        These are mean salaries. The work-permit floor
        {floor != null && <> ({sek(floor)})</>} comes from the national median and is the same in every area.
      </p>
      {a.regional.length === 0 ? (
        <p>SCB publishes no regional figures for this code.</p>
      ) : (
        <>
          <table className="w-full text-left">
            <thead className="text-xs text-muted">
              <tr><th scope="col">Area</th><th scope="col">Mean</th><th scope="col">Employees</th></tr>
            </thead>
            <tbody>
              {a.regional.map((r) => (
                <tr key={r.region} className="border-t border-line">
                  <th scope="row" className="font-normal">{r.region_name}</th>
                  <td>{r.mean == null ? np : <>{sek(r.mean)}{r.mean_ci95 != null && <span className="text-muted"> ± {n(r.mean_ci95)}</span>}</>}</td>
                  <td>{r.employees == null ? np : n(r.employees)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-xs text-muted">
            SCB TAB5696 (Medlingsinstitutet / SCB), all sectors, {a.regional_year}, {fetched(a.regional.map((r) => r.fetched_at))}
          </p>
        </>
      )}
    </section>
  );
}

const CHART_H = 120;
const LABEL_H = 18;

/** One series, so no legend (dataviz skill); bars rise from a common baseline, 4 px rounded tops. */
function YearBars({ rows }: { rows: YearlyAds[] }) {
  const { ref, width } = useWidth();
  const max = Math.max(1, ...rows.map((r) => r.ads));
  const band = width / rows.length;
  const bar = Math.max(4, band * 0.6);
  const y = (v: number) => CHART_H - (v / max) * (CHART_H - LABEL_H);
  const every = band < 36 ? 2 : 1; // year labels need about 32 px each
  const peak = rows.findIndex((r) => r.ads === max);
  return (
    <div ref={ref}>
      <svg width={width} height={CHART_H + LABEL_H} role="img"
        aria-label={`Ads published per year, ${rows[0].year} to ${rows.at(-1)!.year}`}>
        <line x1={0} x2={width} y1={CHART_H} y2={CHART_H} stroke="var(--color-axis)" strokeWidth={1} />
        {rows.map((r, i) => {
          const x = i * band + (band - bar) / 2;
          const top = y(r.ads);
          const h = CHART_H - top;
          const rr = Math.min(4, h);
          return (
            <g key={r.year} data-testid="year-bar">
              <title>{`${r.year}: ${n(r.ads)} ads`}</title>
              {h > 0 && (
                <path fill="var(--color-bar)" d={`M${x},${CHART_H} V${top + rr} Q${x},${top} ${x + rr},${top}
                  H${x + bar - rr} Q${x + bar},${top} ${x + bar},${top + rr} V${CHART_H} Z`} />
              )}
              {(i === peak || i === rows.length - 1 || r.ads === 0) && (
                <text x={i === rows.length - 1 ? x + bar : x + bar / 2} y={top - 4} fontSize={11}
                  textAnchor={i === rows.length - 1 ? "end" : "middle"} fill="var(--color-ink)">{n(r.ads)}</text>
              )}
              {i % every === 0 && (
                <text x={x + bar / 2} y={CHART_H + 14} fontSize={11} textAnchor="middle" fill="var(--color-muted)">{r.year}</text>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function AdsPerYear({ a }: { a: MarketAnswer }) {
  return (
    <section aria-label="Ads per year" className="space-y-1">
      <h5 className="text-xs font-semibold uppercase text-muted">Ads published per year (Platsbanken)</h5>
      {a.history_status === "no_concept" ? <p>{NO_CONCEPT}</p> : (
        <>
          <Shared a={a} />
          <YearBars rows={a.history} />
          <details>
            <summary className="cursor-pointer text-muted">Table</summary>
            <table className="text-left">
              <thead className="text-xs text-muted"><tr><th scope="col">Year</th><th scope="col">Ads</th></tr></thead>
              <tbody>{a.history.map((h) => <tr key={h.year}><td>{h.year}</td><td>{n(h.ads)}</td></tr>)}</tbody>
            </table>
          </details>
          <p className="text-xs text-muted">
            Arbetsförmedlingen historical ads, full years, {a.history.length > 0 && fetched(a.history.map((h) => h.fetched_at))}
          </p>
        </>
      )}
    </section>
  );
}

/** Market context for one code (Feature 005): open ads now, mean pay by area and ads per year.
 * Context only: it never ranks codes, and every figure comes from the API. */
export function MarketPanel({ code, floor }: { code: string; floor: number | null }) {
  const [answer, setAnswer] = useState<MarketAnswer | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let live = true;
    api.GET("/api/v1/occupations/{code}/market", { params: { path: { code } } }).then(({ data }) => {
      if (!live) return;
      setAnswer(data ?? null);
      setFailed(!data);
    }, () => live && setFailed(true));
    return () => { live = false; };
  }, [code]);
  return (
    <section aria-label={`Market for ${code}`} className="space-y-3 border-t border-line pt-3 text-sm">
      <h4 className="font-semibold">Market</h4>
      {failed && <Notice kind="error">The market data could not be loaded.</Notice>}
      {answer && (
        <>
          <p className="text-xs text-muted">{answer.notice}</p>
          <OpenNow a={answer} />
          <PayByArea a={answer} floor={floor} />
          <AdsPerYear a={answer} />
        </>
      )}
    </section>
  );
}
