import { type ReactNode, useEffect, useState } from "react";
import { api, type EligibilityAnswer, type Offer, type Registry, type TimelineEvent } from "../api/client";
import { EligibilityResult } from "../components/EligibilityResult";
import { OfferPanel } from "../components/OfferPanel";
import { sek } from "../components/SalaryChart";
import { SourceLink } from "../components/SourceLink";
import type { Draft } from "../lib/offer";

// Every figure, date and legal sentence here comes from the API's legal registry and timeline
// (FR-013); the page adds headings and labels only.
const LIST_NAMES: Record<string, string> = {
  exempt_75: "Exempt codes: a lower share of the median applies",
  banned: "Banned codes: no work permit can be granted",
  partially_banned: "Partly banned codes",
};

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section aria-label={title} className="space-y-2 rounded border border-line bg-panel p-3">
      <h3 className="font-semibold">{title}</h3>
      {children}
    </section>
  );
}

const span = (from?: string | null, to?: string | null) =>
  from && to ? `${from} to ${to}` : from ? `from ${from}` : to ? `until ${to}` : "";

type Props = {
  registry: Registry | null;
  draft: Draft;
  onApplied: (draft: Draft, offer: Offer, answer: EligibilityAnswer) => void;
};

export function LegalView({ registry, draft, onApplied }: Props) {
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [code, setCode] = useState("");
  const [answer, setAnswer] = useState<EligibilityAnswer | null>(null);
  useEffect(() => {
    api.GET("/api/v1/legal/timeline").then(({ data }) => data && setTimeline(data));
  }, []);
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">The salary requirement</h2>
      <p className="text-sm text-muted">
        A work permit offer must pay at least a set share of the latest SCB median salary. The rules,
        figures and dates below come from Lönekrav's legal registry, each with its source and the date it
        was checked. This is information, not legal advice.
      </p>
      <Section title="Check an offer">
        <div className="flex flex-col gap-0.5">
          <label htmlFor="calc-code" className="text-sm">SSYK code (4 digits)</label>
          <input id="calc-code" value={code} onChange={(e) => setCode(e.target.value.trim())} inputMode="numeric"
            className="w-32 rounded border border-line bg-panel px-2 py-1 font-mono" />
        </div>
        <OfferPanel code={code} draft={draft} exemptions={Object.values(registry?.exemptions ?? {})}
          submitLabel="Check this offer" onApplied={(d, o, a) => { setAnswer(a); onApplied(d, o, a); }} />
        {answer && (
          <section aria-label="Result" className="border-t border-line pt-3">
            <EligibilityResult answer={answer} />
          </section>
        )}
      </Section>
      {registry && (
        <>
          <Section title="The rules">
            <ul className="space-y-2 text-sm">
              {Object.values(registry.rules).map((r) => (
                <li key={r.id}>
                  <strong>{r.kind === "flat" && r.amount != null ? sek(r.amount) : `${r.percent} % of the median`}</strong>
                  {" "}<span className="text-muted">({span(r.effective_from, r.effective_to)})</span>. {r.applies_to}{" "}
                  <SourceLink source={r.source} />
                </li>
              ))}
            </ul>
          </Section>
          <Section title="SCB medians">
            <table className="w-full text-left text-sm tabular-nums">
              <thead className="text-xs text-muted"><tr><th>Median</th><th>SCB year</th><th>Applies</th></tr></thead>
              <tbody>
                {registry.medians.map((m) => (
                  <tr key={m.effective_from}>
                    <td>{sek(m.amount)}</td><td>{m.scb_reference_year}</td><td>{span(m.effective_from, m.effective_to)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <SourceLink source={registry.medians.at(-1)!.source} />
          </Section>
          <Section title="Codes with their own rules">
            {Object.entries(registry.code_lists).map(([kind, cl]) => (
              <div key={kind} className="space-y-1">
                <h4 className="text-sm font-semibold">{LIST_NAMES[kind] ?? kind}</h4>
                <p className="text-sm">{cl.note} <span className="text-muted">({span(cl.effective_from, cl.effective_to)})</span>{" "}
                  <SourceLink source={cl.source} /></p>
                <ul className="grid gap-x-4 text-sm sm:grid-cols-2">
                  {Object.entries(cl.codes).map(([c, title]) => (
                    <li key={c}><span className="font-mono">{c}</span> <span lang="sv">{title}</span></li>
                  ))}
                </ul>
              </div>
            ))}
          </Section>
          <Section title="Personal exemptions">
            <ul className="space-y-1 text-sm">
              {Object.values(registry.exemptions).map((x) => (
                <li key={x.id}><strong>{x.label}</strong>. {x.conditions}
                  {x.first_permit_only && " First permits only."} <SourceLink source={x.source} /></li>
              ))}
            </ul>
          </Section>
          <Section title="Good to know">
            <ul className="space-y-1 text-sm">
              {Object.values(registry.statements).map((st) => (
                <li key={st.id}><span>{st.text}</span> <SourceLink source={st.source} /></li>
              ))}
            </ul>
          </Section>
        </>
      )}
      <Section title="Timeline">
        <ol aria-label="Timeline" className="space-y-1 text-sm">
          {timeline.map((e) => (
            <li key={`${e.date}-${e.summary}`} className="grid grid-cols-[6.5rem_1fr] gap-2">
              <span className="tabular-nums text-muted">{e.date}</span>
              <span>{e.summary} <SourceLink source={e.source} /></span>
            </li>
          ))}
        </ol>
      </Section>
    </div>
  );
}
