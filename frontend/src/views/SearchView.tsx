import { type Dispatch, useEffect, useMemo, useState } from "react";
import { AdPassages } from "../components/AdPassages";
import { Notice } from "../components/Notice";
import { ResultList } from "../components/ResultList";
import { apiSearch, SearchSession, type SessionState } from "../lib/searchSession";
import type { Action, Selection } from "../lib/selection";
import type { AgeBand } from "../lib/urlState";

export type SearchViewProps = {
  selection: Selection;
  dispatch: Dispatch<Action>;
  age: AgeBand | null;
  setAge: (age: AgeBand | null) => void;
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

export function SearchView({ selection, dispatch }: SearchViewProps) {
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
        <>
          <AdPassages answer={state.answer} />
          <ResultList answer={state.answer} selected={selection.codes}
            onSelect={(code) => dispatch({ type: "add", code })} />
        </>
      )}
    </>
  );
}
