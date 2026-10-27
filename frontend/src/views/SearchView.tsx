import { type Dispatch, useEffect, useMemo, useState } from "react";
import { AdPassages } from "../components/AdPassages";
import { Notice } from "../components/Notice";
import { ResultList } from "../components/ResultList";
import { apiSearch, SearchSession, type SessionState } from "../lib/searchSession";
import type { Action, Selection } from "../lib/selection";

export type SearchViewProps = {
  selection: Selection;
  dispatch: Dispatch<Action>;
  onNext: () => void; // on to step 2, Your number, where the selected codes' pay is shown
};

function useSearch() {
  const [state, setState] = useState<SessionState | null>(null);
  const session = useMemo(() => new SearchSession(apiSearch, setState), []);
  useEffect(() => () => session.setText(""), [session]); // abort anything in flight on unmount
  return { state, setText: (t: string) => session.setText(t) };
}

function Status({ state }: { state: SessionState }) {
  const { answer, shown, refining } = state;
  if (!answer) return refining ? <p className="text-sm text-muted">Searching…</p> : null;
  const which = shown === "full" && answer.mode_used === "full" ? "Accurate results" : "Fast results";
  return (
    <p className="text-sm text-muted" aria-live="polite">
      {which}
      {refining && " · refining with the accurate model…"}
      {answer.fallback_reason && ` · the accurate search did not run: ${answer.fallback_reason}`}
    </p>
  );
}

/** The selected codes, removable, and the step on to Your number (006 contracts/ui.md). */
function Selected({ selection, dispatch, onNext }: SearchViewProps) {
  return (
    <section aria-label="Selected codes" className="space-y-2">
      {selection.codes.length ? (
        <div className="flex flex-wrap items-center gap-2">
          {selection.codes.map((code) => (
            <span key={code} className="flex items-center gap-2 rounded-full border border-line bg-panel px-3 py-1 text-sm">
              <span className="font-mono">{code}</span>
              <button type="button" aria-label={`Remove ${code}`} onClick={() => dispatch({ type: "remove", code })}
                className="text-muted hover:text-ink">×</button>
            </span>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted">Add the codes whose duties match the job (up to four).</p>
      )}
      <button type="button" disabled={!selection.codes.length} onClick={onNext}
        className="rounded bg-accent px-3 py-1.5 text-sm text-white disabled:opacity-50">
        Next: your number →
      </button>
    </section>
  );
}

export function SearchView(props: SearchViewProps) {
  const { selection, dispatch } = props;
  const [text, setText] = useState("");
  const search = useSearch();
  const state = search.state;
  return (
    <>
      <section className="space-y-2">
        <h2 className="text-xl font-semibold">Find the codes that fit a job</h2>
        <label htmlFor="q" className="block text-sm">
          Job title or ad <span className="text-muted">(type a title, or paste a whole ad in any language)</span>
        </label>
        <textarea id="q" value={text} rows={text.includes("\n") ? 8 : 2}
          onChange={(e) => { setText(e.target.value); search.setText(e.target.value); }}
          className="w-full rounded border border-line bg-panel p-2" />
        {state && <Status state={state} />}
        {state?.error && <Notice kind="error">{state.error}</Notice>}
        {state?.answer?.low_confidence && (
          <Notice kind="warn">These matches are weak: try a fuller description of the duties.</Notice>
        )}
      </section>
      {state?.answer && (
        <div data-answer-for={state.answerFor ?? ""} className="space-y-6">
          <AdPassages answer={state.answer} />
          <ResultList answer={state.answer} selected={selection.codes}
            onSelect={(code) => dispatch({ type: "add", code })} />
        </div>
      )}
      <Selected {...props} />
    </>
  );
}
