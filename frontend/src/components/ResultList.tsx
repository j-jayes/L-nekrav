import type { LegalFlag, SearchAnswer } from "../api/client";
import { ScoreStrip } from "./ScoreStrip";

const FLAG: Record<LegalFlag["kind"], string> = {
  exempt_75: "Exempt code: a lower salary level applies",
  banned: "Permits cannot be granted for this code",
  partially_banned: "Permits are banned for part of this code",
};

export function Flags({ flags }: { flags: LegalFlag[] }) {
  if (!flags.length) return null;
  return (
    <ul className="space-y-1 text-sm">
      {flags.map((f) => (
        <li key={f.kind} className="border-l-4 border-warn pl-2">
          <strong>{FLAG[f.kind]}.</strong> {f.note}{" "}
          <a className="text-xs text-accent underline" href={f.source.url} target="_blank" rel="noreferrer">
            {f.source.ref}
          </a>
          {f.checked_on && <span className="text-xs text-muted">, checked {f.checked_on}</span>}
        </li>
      ))}
    </ul>
  );
}

type Props = { answer: SearchAnswer; selected: string[]; onSelect: (code: string) => void };

/** The ranked codes, in the API's order (FR-004, FR-012). */
export function ResultList({ answer, selected, onSelect }: Props) {
  return (
    <section aria-label="Matching occupations" className="space-y-3">
      <p className="text-sm text-muted">{answer.honest_fit}</p>
      {answer.hits.map((h) => {
        const on = selected.includes(h.code);
        return (
          <article key={h.code} aria-label={`${h.code} ${h.title_en}`} className="space-y-2 rounded border border-line bg-panel p-3">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <h3 className="font-semibold">
                  <span className="font-mono">{h.code}</span> {h.title_en}
                </h3>
                <p className="text-sm text-muted" lang="sv">{h.title_sv}</p>
              </div>
              <button type="button" disabled={on} onClick={() => onSelect(h.code)}
                aria-label={on ? `${h.code} is on chart` : `Add ${h.code} to chart`}
                className="rounded border border-accent px-2 py-1 text-sm text-accent disabled:border-line disabled:text-muted">
                {on ? "On chart" : "Add to chart"}
              </button>
            </div>
            <p className="line-clamp-2 text-sm">
              <span className="text-muted">Matched: </span>
              {h.matched_chunk.text}
            </p>
            <Flags flags={h.legal_flags ?? []} />
            <details className="text-sm">
              <summary className="cursor-pointer text-muted">How this was matched</summary>
              <div className="mt-1"><ScoreStrip hit={h} /></div>
            </details>
          </article>
        );
      })}
    </section>
  );
}
