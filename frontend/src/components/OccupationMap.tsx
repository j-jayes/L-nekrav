// The occupation map (007 US2, US3; contracts/ui.md). Each point is an SSYK code, placed by UMAP
// from the multilingual model's vectors of its official title and descriptions; codes near each
// other describe similar work. Every point is neutral grey with its major group named on the map:
// ten groups are more hues than a scatter can keep apart (dataviz skill, all-pairs check), so
// colour marks only the codes in play, from the three slots that pass it: search hits (outlined,
// bar blue), selected codes (filled, dot orange) and their five nearest neighbours (near aqua).
// Pay is never encoded; it appears only in the readout for one point.
import { useEffect, useRef, useState } from "react";
import { api, type Closeness, type MapAnswer } from "../api/client";
import { fit, IDENTITY, nearest, pan, project, type View, zoomAt } from "../lib/mapScale";
import { sek, useWidth } from "./SalaryChart";

type Point = MapAnswer["points"][number];
const PAD = 24;
const SAME_DESCRIPTION = 0.99; // as core.occupation_map.SAME_DESCRIPTION
const HIT_RADIUS = 14;
const FLAG: Record<string, string> = {
  exempt_75: "exempt code", banned: "permits cannot be granted", partially_banned: "partly banned",
};

function useCloseness(a: string | undefined, b: string | undefined) {
  const [answer, setAnswer] = useState<Closeness | null>(null);
  useEffect(() => {
    setAnswer(null);
    if (!a || !b || a === b) return;
    let live = true;
    api.GET("/api/v1/closeness", { params: { query: { a, b } } }).then(({ data }) => live && setAnswer(data ?? null));
    return () => { live = false; };
  }, [a, b]);
  return answer;
}

function Readout({ points, selected, groups }: { points: Point[]; selected: string | undefined;
  groups: MapAnswer["major_groups"] }) {
  const near = useCloseness(selected, points[0]?.code);
  if (!points.length) return <>Hover, tap or tab to a point to read it. Drag to move, scroll or use the buttons to zoom.</>;
  return (
    <div className="space-y-1">
      {points.map((p) => (
        <p key={p.code}>
          <span className="font-mono font-semibold">{p.code}</span> {p.title_en}{" "}
          <span className="text-muted" lang="sv">{p.title_sv}</span>
          {" · "}{groups[p.major_group]?.en}
          {" · "}{p.median_sek != null ? `Median ${sek(p.median_sek)} (SCB ${p.median_year})` : "SCB publishes no median"}
          {p.legal_flags.map((f) => <span key={f} className="text-warn"> · {FLAG[f] ?? f}</span>)}
        </p>
      ))}
      {near && (near.same_description
        ? <p>Same official description as {selected}: the text cannot tell them apart, the classification does.</p>
        : <p>Closer to {selected} than {near.percentile} % of pairs of occupations (similarity {near.cosine}).</p>)}
    </div>
  );
}

type Props = {
  map: MapAnswer;
  hits: string[]; // the current search results, outlined
  selected: string[]; // filled, with lines to their five nearest neighbours
  onSelect: (code: string) => void;
};

export function OccupationMap({ map, hits, selected, onSelect }: Props) {
  const { ref, width } = useWidth();
  const height = Math.round(Math.min(width * 0.7, 520));
  const [view, setView] = useState<View>(IDENTITY);
  const [shown, setShown] = useState<string[]>([]);
  const [asTable, setAsTable] = useState(false);
  const svg = useRef<SVGSVGElement>(null);
  const drag = useRef<{ x: number; y: number; moved: number } | null>(null);
  const byCode = new Map(map.points.map((p) => [p.code, p]));
  const at = (p: Point) => project(p, IDENTITY, width, height, PAD); // inside the zoom layer
  // A code and the codes that share its official description (cosine >= 0.99, 007 FR-009): UMAP
  // draws them a few pixels apart, so they are read together.
  const stack = (code: string) => [code, ...(byCode.get(code)?.neighbours ?? [])
    .filter((n) => n.cosine >= SAME_DESCRIPTION && n.code !== code).map((n) => n.code)];
  const under = (x: number, y: number) => {
    const at = nearest(map.points, view, width, height, PAD, x, y, HIT_RADIUS);
    return at.length ? [...new Set(at.flatMap(stack))] : [];
  };
  // Each code is drawn once: selected, else search result, else neighbour of a selected code.
  const outlined = hits.filter((c) => !selected.includes(c) && byCode.has(c));
  const near = [...new Set(selected.flatMap((c) => (byCode.get(c)?.neighbours ?? []).slice(0, 5).map((n) => n.code)))]
    .filter((c) => !selected.includes(c) && !outlined.includes(c));

  useEffect(() => { // wheel zoom needs a non-passive listener to keep the page from scrolling
    const el = svg.current;
    if (!el) return;
    const wheel = (e: WheelEvent) => {
      e.preventDefault();
      const r = el.getBoundingClientRect();
      setView((v) => zoomAt(v, e.deltaY < 0 ? 1.2 : 1 / 1.2, e.clientX - r.left, e.clientY - r.top));
    };
    el.addEventListener("wheel", wheel, { passive: false });
    return () => el.removeEventListener("wheel", wheel);
  }, []);

  const local = (e: React.PointerEvent) => {
    const r = svg.current!.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  };
  const onMove = (e: React.PointerEvent) => {
    const p = local(e);
    if (drag.current) {
      const dx = p.x - drag.current.x;
      const dy = p.y - drag.current.y;
      drag.current = { x: p.x, y: p.y, moved: drag.current.moved + Math.abs(dx) + Math.abs(dy) };
      setView((v) => pan(v, dx, dy));
      return;
    }
    setShown(under(p.x, p.y));
  };
  const onUp = (e: React.PointerEvent) => {
    const moved = drag.current?.moved ?? 0;
    drag.current = null;
    if (moved > 4) return; // a drag, not a tap
    const p = local(e);
    const codes = under(p.x, p.y);
    setShown(codes);
    if (codes.length) onSelect(codes[0]);
  };

  const k = view.k;
  const focusable = (code: string, role: string, mark: React.ReactNode, label = true) => {
    const p = byCode.get(code)!;
    const { px, py } = at(p);
    return (
      <g key={`${role}-${code}`} role="button" tabIndex={0} aria-label={`${code} ${p.title_en} (${role})`}
        onFocus={() => setShown(stack(code))}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelect(code); } }}
        className="cursor-pointer outline-none focus-visible:[&>circle]:stroke-[var(--color-ink)]">
        {mark}
        {label && (
          <text data-testid="point-label" x={px + 7 / k} y={py - 6 / k} fontSize={11 / k} fill="var(--color-ink)"
            paintOrder="stroke" stroke="var(--color-page)" strokeWidth={3 / k}>{code}</text>
        )}
      </g>
    );
  };
  const button = "rounded border border-line bg-panel px-2 py-0.5 text-sm";
  return (
    <figure className="space-y-2 rounded border border-line bg-panel p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <ul aria-label="Legend" className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted">
          <li className="flex items-center gap-1"><svg width="12" height="12" aria-hidden><circle cx="6" cy="6" r="4" fill="var(--color-page)" stroke="var(--color-bar)" strokeWidth="2" /></svg>Search results</li>
          <li className="flex items-center gap-1"><svg width="12" height="12" aria-hidden><circle cx="6" cy="6" r="5" fill="var(--color-dot)" /></svg>Selected</li>
          <li className="flex items-center gap-1"><svg width="12" height="12" aria-hidden><circle cx="6" cy="6" r="4" fill="var(--color-near)" /></svg>Most similar to a selected code</li>
        </ul>
        <div className="flex gap-1">
          <button type="button" aria-label="Zoom in" className={button} onClick={() => setView((v) => zoomAt(v, 1.5, width / 2, height / 2))}>+</button>
          <button type="button" aria-label="Zoom out" className={button} onClick={() => setView((v) => zoomAt(v, 1 / 1.5, width / 2, height / 2))}>−</button>
          <button type="button" className={button} disabled={!selected.some((c) => byCode.has(c))}
            aria-label="Zoom to the selected codes"
            onClick={() => setView(fit([...selected, ...near].filter((c) => byCode.has(c)).map((c) => byCode.get(c)!),
              width, height, PAD, 40))}>Selected</button>
          <button type="button" aria-label="Reset the view" className={button} onClick={() => setView(IDENTITY)}>Reset</button>
        </div>
      </div>
      <div ref={ref} aria-hidden className="h-0" />
      <svg ref={svg} width={width} height={height} viewBox={`0 0 ${width} ${height}`} role="group"
        aria-label="Map of occupations by similarity of their official descriptions"
        className="block touch-none select-none overflow-hidden rounded bg-page"
        onPointerDown={(e) => { const p = local(e); drag.current = { ...p, moved: 0 }; }}
        onPointerMove={onMove} onPointerUp={onUp} onPointerLeave={() => { drag.current = null; }}>
        <g data-testid="zoom-layer" transform={`translate(${view.tx} ${view.ty}) scale(${view.k})`}>
          {map.points.map((p) => {
            const { px, py } = at(p);
            return <circle key={p.code} data-testid="point" cx={px} cy={py} r={2.5 / k} fill="var(--color-axis)" />;
          })}
          {selected.filter((c) => byCode.has(c)).flatMap((c) => (byCode.get(c)!.neighbours.slice(0, 5)).map((n) => {
            const a = at(byCode.get(c)!);
            const b = at(byCode.get(n.code)!);
            return <line key={`${c}-${n.code}`} data-testid="link" data-to={n.code} x1={a.px} y1={a.py} x2={b.px} y2={b.py}
              stroke="var(--color-muted)" strokeWidth={1.5 / k} />;
          }))}
          {near.map((c) => focusable(c, "similar to a selected code", (() => {
            const { px, py } = at(byCode.get(c)!);
            return <circle data-testid="near" cx={px} cy={py} r={4.5 / k} fill="var(--color-near)" stroke="var(--color-page)" strokeWidth={1.5 / k} />;
          })(), false))}
          {outlined.map((c) => focusable(c, "search result", (() => {
            const { px, py } = at(byCode.get(c)!);
            return <circle data-testid="hit" cx={px} cy={py} r={5 / k} fill="var(--color-page)" stroke="var(--color-bar)" strokeWidth={2 / k} />;
          })()))}
          {selected.filter((c) => byCode.has(c)).map((c) => focusable(c, "selected", (() => {
            const { px, py } = at(byCode.get(c)!);
            return <circle data-testid="selected" cx={px} cy={py} r={6 / k} fill="var(--color-dot)" stroke="var(--color-page)" strokeWidth={2 / k} />;
          })()))}
        </g>
      </svg>
      <div role="status" className="min-h-10 text-sm">
        <Readout points={shown.map((c) => byCode.get(c)!).filter(Boolean)} selected={selected[0]}
          groups={map.major_groups} />
      </div>
      <figcaption className="text-xs text-muted">
        Each point is an occupation, placed by how similar its official description is to the others
        (multilingual model, then UMAP). Distances on the map are approximate; the similarity figures
        are exact. Similar descriptions never decide which code fits: the duties do.
      </figcaption>
      <div>
        <button type="button" className="text-sm text-accent underline" aria-expanded={asTable}
          onClick={() => setAsTable(!asTable)}>{asTable ? "Hide the table" : "Show as a table"}</button>
        <div className={asTable ? "mt-2 max-h-96 overflow-auto" : "sr-only"}>
          <table aria-label="Occupations and their nearest five" className="w-full text-left text-sm [&_td]:py-0.5 [&_td]:pr-3">
            <thead className="text-xs text-muted"><tr><th>Code</th><th>Occupation</th><th>Group</th><th>Nearest five</th></tr></thead>
            <tbody>
              {map.points.map((p) => (
                <tr key={p.code}>
                  <td className="font-mono">{p.code}</td><td>{p.title_en}</td>
                  <td>{map.major_groups[p.major_group]?.en}</td>
                  <td className="font-mono">{p.neighbours.slice(0, 5).map((n) => n.code).join(", ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </figure>
  );
}
