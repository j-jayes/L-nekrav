import type { SearchHit } from "../api/client";

// The search methods (core.search.METHODS) in words; a method missing from `ranks` did not run.
export const METHODS = [
  { key: "kblab", label: "Swedish model" },
  { key: "bm25", label: "Keywords" },
  { key: "harrier", label: "Accurate model" },
] as const;

export function ScoreStrip({ hit }: { hit: SearchHit }) {
  return (
    <ul aria-label="Rank by search method" className="flex flex-wrap gap-1 text-xs">
      {METHODS.map(({ key, label }) => {
        const rank = hit.ranks[key];
        return (
          <li key={key} className={`rounded border border-line px-1.5 py-0.5 ${rank == null ? "text-muted" : ""}`}>
            <span>{label}</span>
            <span className="ml-1 font-mono">{rank == null ? "not run" : `#${rank}`}</span>
          </li>
        );
      })}
    </ul>
  );
}
