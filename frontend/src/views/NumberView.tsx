// Step 2, "Your number" (006 US1, US2, US4; contracts/ui.md). The candidate types the monthly
// salary they plan to ask for; each selected code shows SCB's published middle half and median,
// where the number sits among them, an estimate for their age band and area (not an SCB figure),
// and the floor check under it. Cards keep the order selected and are never ranked by pay.
import { type Dispatch, useEffect, useRef, useState } from "react";
import { api, type CompareColumn, type Comparison, type Closeness, type EligibilityAnswer, type NeighbourAnswer,
  type Registry, type SalaryPayload, type Source } from "../api/client";
import { EligibilityResult } from "../components/EligibilityResult";
import { MarketPanel } from "../components/MarketPanel";
import { Notice } from "../components/Notice";
import { OfferForm } from "../components/OfferForm";
import { Flags } from "../components/ResultList";
import { estimateLabel, SalaryChart, sek } from "../components/SalaryChart";
import { SourceLink } from "../components/SourceLink";
import { type Draft, fieldErrors, offerFrom, parseNumber } from "../lib/offer";
import type { Action, Selection } from "../lib/selection";
import { AGE_BANDS, type AgeBand, type Region, REGIONS } from "../lib/urlState";

type Position = NonNullable<EligibilityAnswer["market_position"]>;
type Ref = NonNullable<Position["lower"]>;
type Text = CompareColumn["tasks_sv"][number];
type Errors = Partial<Record<keyof Draft | "form", string>>;

const NAME: Record<Ref["name"], string> = {
  p10: "10th percentile", p25: "25th percentile", median: "median", p75: "75th percentile", p90: "90th percentile",
};
const SOURCE: Record<string, string> = { scb_mis2012: "SCB", jobtech: "JobTech", esco: "ESCO", scb_structure: "SCB" };
const ref = (r: Ref) => `the ${NAME[r.name]} (${sek(r.value_sek)})`;

/** "Your 60 000 SEK is between the median (56 200 SEK) and the 75th percentile (66 700 SEK)." */
export function positionSentence(p: Position, fte: number) {
  if (p.no_data) return "SCB publishes no percentiles for this code, so the number cannot be placed.";
  const you = `Your ${sek(p.amount_sek)}${fte < 100 ? " (full-time equivalent)" : ""}`;
  const where = p.at ? `is at the ${NAME[p.at.name]}`
    : p.lower && p.upper ? `is between ${ref(p.lower)} and ${ref(p.upper)}`
    : p.upper ? `is below ${ref(p.upper)}` : `is above ${ref(p.lower!)}`;
  const gap = p.missing.length
    ? ` SCB publishes no ${p.missing.map((m) => NAME[m]).join(" or ")} for this code, so the nearest published figures are used.` : "";
  return `${you} ${where}.${gap}`;
}

/** "SCB 2025: the middle half earn 47 700–66 700 SEK; median 56 200 SEK." Suppressed figures are named. */
function headline(p: SalaryPayload) {
  const d = p.distributions.at(-1);
  if (!d) return "SCB publishes no salary figures for this code.";
  const middle = d.p25 != null && d.p75 != null ? `the middle half earn ${d.p25.toLocaleString("sv-SE")}–${sek(d.p75)}`
    : `SCB publishes no ${[d.p25 == null && "25th", d.p75 == null && "75th"].filter(Boolean).join(" or ")} percentile`;
  return `SCB ${d.year}: ${middle}; median ${d.median == null ? "not published" : sek(d.median)}.`;
}

function Estimate({ p }: { p: SalaryPayload }) {
  const e = p.simulated;
  if (!e) return p.estimate_note ? <p className="text-xs text-muted">No estimate: {p.estimate_note}.</p> : null;
  const range = e.p25 != null && e.p75 != null ? `${e.p25.toLocaleString("sv-SE")}–${sek(e.p75)}`
    : e.p25 != null ? `from ${sek(e.p25)}` : `up to ${sek(e.p75!)}`;
  return (
    <div data-testid="estimate-chip" className="rounded border border-dashed border-ink px-2 py-1 text-sm">
      <p>{estimateLabel(e)}: <span className="tabular-nums font-semibold">{range}</span>
        <span className="text-muted"> · not an SCB figure</span></p>
      {(e.left_out ?? []).map((lo) => (
        <p key={lo.factor} className="text-xs text-muted">Not adjusted for {lo.factor === "age" ? "age" : "area"}: {lo.reason}.</p>
      ))}
      <details className="text-xs text-muted">
        <summary className="cursor-pointer">How this is estimated</summary>
        <p>{e.formula}</p>
        <p>Inputs: {e.inputs.map((t) => `${t.table} (${t.reference_year})`).join(", ")}</p>
      </details>
    </div>
  );
}

function Tasks({ title, texts, lang }: { title: string; texts: Text[]; lang: "sv" | "en" }) {
  if (!texts.length) return null;
  return (
    <div lang={lang}>
      <h4 className="text-xs font-semibold uppercase text-muted">{title}</h4>
      <ul className="space-y-1">
        {texts.map((t) => (
          <li key={t.text} className="text-sm">
            {t.text}{" "}
            <a href={t.source.url} target="_blank" rel="noreferrer" className="text-xs text-accent underline">
              {SOURCE[t.source.source] ?? t.source.source}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Floor({ p, answer, rules }: { p?: SalaryPayload; answer?: EligibilityAnswer | null; rules?: Registry["rules"] }) {
  if (answer) return (
    <div className="space-y-1">
      <EligibilityResult answer={answer} compact />
      <p className="text-xs">{answer.sources.map((s) => <SourceLink key={s.key} source={s} />)}</p>
    </div>
  );
  const line = p?.thresholds.find((t) => t.rule_id === p.applicable_rule_id);
  if (!p) return null;
  if (!line) return <p className="text-sm">✗ Work permits cannot be granted for this code.</p>;
  return (
    <p className="text-sm">
      Salary floor {sek(line.amount_sek)} ({line.percent} % of the median) ·{" "}
      <SourceLink source={line.source ?? rules?.[line.rule_id]?.source} />
    </p>
  );
}

/** The five occupations whose official descriptions are closest, nearest first (007 FR-013). */
function SimilarWork({ code }: { code: string }) {
  const [answer, setAnswer] = useState<NeighbourAnswer | null>(null);
  useEffect(() => {
    let live = true;
    api.GET("/api/v1/occupations/{code}/neighbours", { params: { path: { code }, query: { k: 5 } } })
      .then(({ data }) => live && setAnswer(data ?? null));
    return () => { live = false; };
  }, [code]);
  if (!answer) return null;
  return (
    <div className="mt-2 space-y-1">
      <ul className="space-y-1">
        {answer.neighbours.map((n) => (
          <li key={n.code}>
            <span className="font-mono">{n.code}</span> {n.title_en}
            <span className="text-muted"> · {n.same_description ? "the same official description"
              : `closer than ${n.percentile} % of pairs`}{n.median_sek != null && ` · median ${sek(n.median_sek)}`}</span>
          </li>
        ))}
      </ul>
      <p className="text-xs text-muted">{answer.honest_fit}</p>
    </div>
  );
}

function PairCloseness({ a, b }: { a: string; b: string }) {
  const [near, setNear] = useState<Closeness | null>(null);
  useEffect(() => {
    let live = true;
    api.GET("/api/v1/closeness", { params: { query: { a, b } } }).then(({ data }) => live && setNear(data ?? null));
    return () => { live = false; };
  }, [a, b]);
  if (!near) return null;
  return (
    <p className="text-sm">
      {near.same_description ? `${a} and ${b} share one official description: the text cannot tell them apart.`
        : `${a} and ${b} have official descriptions closer than ${near.percentile} % of pairs of occupations.`}
    </p>
  );
}

type CardProps = { code: string; payload?: SalaryPayload; column?: CompareColumn; answer?: EligibilityAnswer | null;
  fte: number; rules?: Registry["rules"]; onRemove: () => void; onNotice: (n: string) => void };

function Card({ code, payload, column, answer, fte, rules, onRemove, onNotice }: CardProps) {
  const title = payload ?? column;
  return (
    <article aria-label={`${code} ${title?.title_en ?? ""}`} className="space-y-2 rounded border border-line bg-panel p-3">
      <header className="flex items-start justify-between gap-2">
        <div>
          <h3 className="font-semibold"><span className="font-mono">{code}</span> {title?.title_en}</h3>
          <p className="text-sm text-muted" lang="sv">{title?.title_sv}</p>
        </div>
        <button type="button" aria-label={`Remove ${code}`} onClick={onRemove} className="text-muted hover:text-ink">×</button>
      </header>
      {payload && <p data-testid="headline" className="text-sm">{headline(payload)}</p>}
      {answer?.market_position && <p className="font-semibold">{positionSentence(answer.market_position, fte)}</p>}
      {payload && <Estimate p={payload} />}
      <Floor p={payload} answer={answer} rules={rules} />
      {column && <Flags flags={column.legal_flags} />}
      <details className="text-sm">
        <summary className="cursor-pointer text-accent">What the work is</summary>
        <div className="mt-2 space-y-2">
          {column && <Tasks title="Official tasks (Swedish)" texts={column.tasks_sv} lang="sv" />}
          {column && <Tasks title="Tasks in English" texts={column.tasks_en} lang="en" />}
        </div>
      </details>
      <details className="text-sm">
        <summary className="cursor-pointer text-accent">Similar work</summary>
        <SimilarWork code={code} />
      </details>
      <details className="text-sm">
        <summary className="cursor-pointer text-accent">Market</summary>
        <MarketPanel code={code} floor={answer?.threshold_sek ?? column?.threshold?.amount_sek ?? null} onNotice={onNotice} />
      </details>
    </article>
  );
}

/** Each code's salary payload for the age band and area, again when either changes. */
function usePayloads(codes: string[], age: AgeBand | null, region: Region | null, payloads: Selection["payloads"],
  dispatch: Dispatch<Action>) {
  // The age band and area each code's payload was requested for, and which requests are still out.
  const requested = useRef(new Map<string, string>());
  const pending = useRef(new Set<string>());
  useEffect(() => {
    const key = `${age ?? ""}|${region ?? ""}`;
    for (const code of codes) {
      if (requested.current.get(code) === key && (payloads[code] || pending.current.has(code))) continue;
      requested.current.set(code, key);
      pending.current.add(code);
      api.GET("/api/v1/occupations/{code}/salary", {
        params: { path: { code }, query: { ...(age ? { age_band: age } : {}), ...(region ? { region } : {}) } },
      }).then(({ data }) => {
        if (data && requested.current.get(code) === key) dispatch({ type: "payload", code, payload: data });
      }).finally(() => pending.current.delete(code));
    }
  }, [codes, age, region, payloads, dispatch]);
}

function useCompare(codes: string[]) {
  const [answer, setAnswer] = useState<Comparison | null>(null);
  const key = codes.join(",");
  useEffect(() => {
    if (!key) return setAnswer(null);
    let live = true;
    api.POST("/api/v1/compare", { body: { codes: key.split(",") } }).then(({ data }) => live && setAnswer(data ?? null));
    return () => { live = false; };
  }, [key]);
  return answer;
}

/** The floor check and market position for each code, a moment after the number stops changing. */
function useEligibility(codes: string[], draft: Draft) {
  const [answers, setAnswers] = useState<Record<string, EligibilityAnswer | null>>({});
  const [errors, setErrors] = useState<Errors>({});
  const offer = offerFrom(draft);
  const key = JSON.stringify([codes, offer]);
  useEffect(() => {
    const [cs, o] = JSON.parse(key) as [string[], ReturnType<typeof offerFrom>];
    if (!o) { setAnswers({}); setErrors({}); return; }
    let live = true;
    const t = setTimeout(() => {
      Promise.all(cs.map((code) => api.POST("/api/v1/eligibility", { body: { ...o, code } }).then((r) => [code, r] as const)))
        .then((pairs) => {
          if (!live) return;
          setAnswers(Object.fromEntries(pairs.map(([c, r]) => [c, r.data ?? null])));
          const bad = pairs.find(([, r]) => r.response.status === 422)?.[1].error;
          setErrors(bad && "detail" in bad && Array.isArray(bad.detail) ? fieldErrors(bad.detail as never) : {});
        });
    }, 300);
    return () => { live = false; clearTimeout(t); };
  }, [key]);
  return { answers, errors };
}

function LegalSources({ answers, payloads, rules }: { answers: (EligibilityAnswer | null)[]; payloads: SalaryPayload[];
  rules?: Registry["rules"] }) {
  const given = answers.filter((a): a is EligibilityAnswer => a != null);
  const sources: Source[] = given.length ? given.flatMap((a) => a.sources)
    : payloads.flatMap((p) => p.thresholds.filter((t) => t.rule_id === p.applicable_rule_id)
      .map((t) => t.source ?? rules?.[t.rule_id]?.source).filter((s): s is Source => s != null));
  const unique = [...new Map(sources.map((s) => [s.key, s])).values()];
  return (
    <section aria-label="Legal sources" className="space-y-1 text-sm">
      <h3 className="text-xs font-semibold uppercase text-muted">Legal sources</h3>
      <ul>{unique.map((s) => <li key={s.key}><SourceLink source={s} /></li>)}</ul>
      <p className="text-xs text-muted">{given[0]?.disclaimer ?? "This is information, not legal advice."}</p>
    </section>
  );
}

export type NumberViewProps = {
  selection: Selection;
  dispatch: Dispatch<Action>;
  age: AgeBand | null;
  setAge: (a: AgeBand | null) => void;
  region: Region | null;
  setRegion: (r: Region | null) => void;
  draft: Draft;
  setDraft: (d: Draft) => void;
  onSearch: () => void;
  rules?: Registry["rules"];
  exemptions: Registry["exemptions"][string][];
};

export function NumberView(props: NumberViewProps) {
  const { selection, dispatch, age, setAge, region, setRegion, draft, setDraft, onSearch, rules, exemptions } = props;
  const { codes, payloads } = selection;
  usePayloads(codes, age, region, payloads, dispatch);
  const comparison = useCompare(codes);
  const { answers, errors } = useEligibility(codes, draft);
  const [notice, setNotice] = useState<string | null>(null);
  const number = parseNumber(draft.monthly_salary_sek);
  const fte = Number(draft.fte_percent) || 100;
  const select = "rounded border border-line bg-panel px-2 py-1";
  if (!codes.length) return (
    <section className="space-y-3">
      <h2 className="text-xl font-semibold">Your number</h2>
      <Notice>
        <button type="button" className="text-accent underline" onClick={onSearch}>Pick the code that matches your duties first</button>
      </Notice>
    </section>
  );
  const shown = codes.map((c) => payloads[c]).filter((p): p is SalaryPayload => p != null);
  return (
    <section className="space-y-3">
      <h2 className="text-xl font-semibold">Your number</h2>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <div className="col-span-2 flex flex-col gap-0.5 sm:col-span-1">
          <label htmlFor="your-number" className="text-sm">Your number (SEK a month)</label>
          <input id="your-number" inputMode="numeric" autoComplete="off" value={draft.monthly_salary_sek}
            onChange={(e) => setDraft({ ...draft, monthly_salary_sek: e.target.value })}
            aria-describedby="your-number-help" aria-invalid={!!number.error} className={select} />
          <p id="your-number-help" className={`text-xs ${number.error ? "text-bad" : "text-muted"}`}>
            {number.error ?? errors.monthly_salary_sek ?? "The monthly salary you plan to ask for, before tax."}
          </p>
        </div>
        <label className="flex flex-col gap-0.5 text-sm">Age
          <select value={age ?? ""} onChange={(e) => setAge((e.target.value || null) as AgeBand | null)} className={select}>
            <option value="">any</option>
            {AGE_BANDS.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-0.5 text-sm">Where the job is
          <select value={region ?? ""} onChange={(e) => setRegion((e.target.value || null) as Region | null)} className={select}>
            <option value="">all of Sweden</option>
            {Object.entries(REGIONS).map(([k, name]) => <option key={k} value={k}>{name}</option>)}
          </select>
        </label>
      </div>
      <details className="rounded border border-line bg-panel p-3 text-sm">
        <summary className="cursor-pointer">Offer details for the floor check</summary>
        <div className="mt-3 space-y-2">
          <p className="text-xs text-muted">Until you change them: full time, a first permit, filed and decided today.</p>
          <OfferForm key={JSON.stringify({ ...draft, monthly_salary_sek: "" })} initial={draft} exemptions={exemptions}
            errors={errors} withSalary={false} submitLabel="Use these details"
            onSubmit={(d) => setDraft({ ...d, monthly_salary_sek: draft.monthly_salary_sek })} />
        </div>
      </details>
      {comparison && <p className="text-sm text-muted">{comparison.honest_fit}</p>}
      {codes.length === 2 && <PairCloseness a={codes[0]} b={codes[1]} />}
      <div className="grid gap-3 md:grid-cols-2">
        {codes.map((code) => (
          <Card key={code} code={code} payload={payloads[code]} column={comparison?.columns.find((c) => c.code === code)}
            answer={answers[code]} fte={fte} rules={rules} onRemove={() => dispatch({ type: "remove", code })}
            onNotice={setNotice} />
        ))}
      </div>
      {notice && <p className="text-xs text-muted">{notice}</p>}
      {shown.length > 0 && (
        <SalaryChart payloads={shown} eligibility={answers} rules={rules}
          number={number.value == null ? null : Math.round((number.value * 100) / fte)} />
      )}
      <LegalSources answers={codes.map((c) => answers[c] ?? null)} payloads={shown} rules={rules} />
    </section>
  );
}
