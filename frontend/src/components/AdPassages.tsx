import type { AdPassage, SearchAnswer } from "../api/client";

const LABEL: Record<AdPassage["label"], string> = {
  title: "job title", duty: "duties", skill: "requirements", company: "company", benefits: "benefits",
  other: "other",
};

function reason(p: AdPassage) {
  if (p.by === "position") return "first line, read as the job title";
  if (p.by === "heading") return `under a ${LABEL[p.label]} heading`;
  return `reads like ${LABEL[p.label]} text`;
}

function Passages({ name, items }: { name: string; items: AdPassage[] }) {
  return (
    <div>
      <h4 className="text-sm font-semibold">{name}</h4>
      <ul aria-label={name} className="mt-1 space-y-1 text-sm">
        {items.map((p) => (
          <li key={p.index}>
            {p.text} <span className="text-xs text-muted">({reason(p)})</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Which parts of a pasted ad the search read, and which it set aside as fluff (FR-003). */
export function AdPassages({ answer }: { answer: SearchAnswer }) {
  const passages = answer.passages;
  if (!passages?.length) return null;
  return (
    <section aria-label="How the ad was read" className="space-y-3 rounded border border-line bg-panel p-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <Passages name="Read by the search" items={passages.filter((p) => p.keep)} />
        <Passages name="Set aside" items={passages.filter((p) => !p.keep)} />
      </div>
      <details className="text-sm">
        <summary className="cursor-pointer text-muted">The text the search used</summary>
        <p className="mt-1 whitespace-pre-wrap">{answer.searched_text}</p>
      </details>
    </section>
  );
}
