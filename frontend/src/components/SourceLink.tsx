import type { Source } from "../api/client";

/** A legal source with its checked-on date (Principle III: every legal statement links its source). */
export function SourceLink({ source }: { source: Pick<Source, "title" | "url" | "checked_on"> }) {
  return (
    <span className="text-xs text-muted">
      <a className="underline text-accent" href={source.url} target="_blank" rel="noreferrer">
        {source.title}
      </a>
      , checked {source.checked_on}
    </span>
  );
}
