import { useEffect, useState } from "react";
import { api, type CompareColumn, type Comparison, type Offer, type Registry, type Source } from "../api/client";
import { EligibilityResult } from "../components/EligibilityResult";
import { MarketPanel } from "../components/MarketPanel";
import { Notice } from "../components/Notice";
import { Flags } from "../components/ResultList";
import { sek } from "../components/SalaryChart";
import { SourceLink } from "../components/SourceLink";

type Text = CompareColumn["tasks_sv"][number];
const SOURCE: Record<string, string> = { scb_mis2012: "SCB", jobtech: "JobTech", esco: "ESCO", scb_structure: "SCB" };

function Tasks({ title, texts, lang }: { title: string; texts: Text[]; lang: "sv" | "en" }) {
  if (!texts.length) return null;
  const [first, ...rest] = texts;
  const item = (t: Text) => (
    <li key={t.text} className="text-sm">
      {t.text}{" "}
      <a href={t.source.url} target="_blank" rel="noreferrer" className="text-xs text-accent underline">
        {SOURCE[t.source.source] ?? t.source.source}
      </a>
    </li>
  );
  return (
    <div lang={lang}>
      <h4 className="text-xs font-semibold uppercase text-muted">{title}</h4>
      <ul className="space-y-1">{item(first)}</ul>
      {rest.length > 0 && (
        <details className="text-sm">
          <summary className="cursor-pointer text-muted">{rest.length} more</summary>
          <ul className="mt-1 space-y-1">{rest.map(item)}</ul>
        </details>
      )}
    </div>
  );
}

function Column({ c }: { c: CompareColumn }) {
  const d = c.latest;
  return (
    <article aria-label={`${c.code} ${c.title_en}`} className="min-w-64 flex-1 space-y-3 rounded border border-line bg-panel p-3">
      <header>
        <h3 className="font-semibold"><span className="font-mono">{c.code}</span> {c.title_en}</h3>
        <p className="text-sm text-muted" lang="sv">{c.title_sv}</p>
      </header>
      {c.eligibility && <EligibilityResult answer={c.eligibility} compact />}
      {!c.eligibility && c.threshold && (
        <p className="text-sm">Floor {sek(c.threshold.amount_sek)} ({c.threshold.percent} % of the median)</p>
      )}
      <Flags flags={c.legal_flags} />
      {d && (
        <p className="text-sm">
          Median {d.median == null ? "not published" : sek(d.median)}; P10–P90{" "}
          {d.p10 == null || d.p90 == null ? "not published" : `${sek(d.p10)} – ${sek(d.p90)}`}
          <span className="text-xs text-muted"> (SCB {d.source_table}, {d.reference_year})</span>
        </p>
      )}
      <Tasks title="Official tasks (Swedish)" texts={c.tasks_sv} lang="sv" />
      <Tasks title="Tasks in English" texts={c.tasks_en} lang="en" />
      <MarketPanel code={c.code} floor={c.eligibility?.threshold_sek ?? c.threshold?.amount_sek ?? null} />
    </article>
  );
}

/** The legal sources behind the columns, once: the eligibility answers' sources with an offer, or
 * each threshold rule's source without one, and the disclaimer (Principle III, FR-016). */
function LegalSources({ answer, rules }: { answer: Comparison; rules?: Registry["rules"] }) {
  const withOffer = answer.columns.map((c) => c.eligibility).filter((e) => e != null);
  const sources: Source[] = withOffer.length
    ? withOffer.flatMap((e) => e.sources)
    : answer.columns.flatMap((c) => (c.threshold && rules?.[c.threshold.rule_id] ? [rules[c.threshold.rule_id].source] : []));
  const unique = [...new Map(sources.map((s) => [s.key, s])).values()];
  return (
    <section aria-label="Legal sources" className="space-y-1 text-sm">
      <h3 className="text-xs font-semibold uppercase text-muted">Legal sources</h3>
      <ul>{unique.map((s) => <li key={s.key}><SourceLink source={s} /></li>)}</ul>
      <p className="text-xs text-muted">
        {withOffer[0]?.disclaimer ?? "This is information, not legal advice."}
      </p>
    </section>
  );
}

type Props = { codes: string[]; offer: Offer | null; onSearch: () => void; rules?: Registry["rules"] };

/** The selected codes side by side, in the order selected, never ranked by threshold (FR-011, FR-012). */
export function CompareView({ codes, offer, onSearch, rules }: Props) {
  const [answer, setAnswer] = useState<Comparison | null>(null);
  const [error, setError] = useState<string | null>(null);
  const enough = codes.length >= 2;
  useEffect(() => {
    if (!enough) return;
    let live = true;
    api.POST("/api/v1/compare", { body: { codes, offer } }).then(({ data, error: e }) => {
      if (!live) return;
      setAnswer(data ?? null);
      setError(e ? "The comparison failed. Check the offer on this page and try again." : null);
    });
    return () => { live = false; };
  }, [codes, offer, enough]);
  return (
    <section className="space-y-3">
      <h2 className="text-xl font-semibold">Compare codes</h2>
      {!enough ? (
        <Notice>
          Comparison needs at least two codes.{" "}
          <button type="button" className="text-accent underline" onClick={onSearch}>Find codes to add</button>
        </Notice>
      ) : (
        <>
          {answer && <p className="text-sm text-muted">{answer.honest_fit}</p>}
          {error && <Notice kind="error">{error}</Notice>}
          <div className="flex flex-col gap-3 md:flex-row md:flex-wrap">
            {answer?.columns.map((c) => <Column key={c.code} c={c} />)}
          </div>
          {answer && <LegalSources answer={answer} rules={rules} />}
        </>
      )}
    </section>
  );
}
