import { type Dispatch, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import { AdPassages } from "../components/AdPassages";
import { Notice } from "../components/Notice";
import { ResultList } from "../components/ResultList";
import { SalaryChart } from "../components/SalaryChart";
import { apiSearch, SearchSession, type SessionState } from "../lib/searchSession";
import type { Action, Selection } from "../lib/selection";
import { AGE_BANDS, type AgeBand } from "../lib/urlState";

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

/** Fetch each selected code's salary payload, again when the age band changes. */
function usePayloads({ selection, dispatch, age }: SearchViewProps) {
  // The age band each code's payload was requested for, and which requests are still out. A code
  // with no SCB data never carries a simulated block, so the request, not the answer, is the key.
  const requested = useRef(new Map<string, string>());
  const pending = useRef(new Set<string>());
  useEffect(() => {
    const band = age ?? "";
    for (const code of selection.codes) {
      const same = requested.current.get(code) === band;
      if (same && (selection.payloads[code] || pending.current.has(code))) continue;
      requested.current.set(code, band);
      pending.current.add(code);
      api.GET("/api/v1/occupations/{code}/salary", {
        params: { path: { code }, query: age ? { age_band: age } : {} },
      }).then(({ data }) => {
        if (data && requested.current.get(code) === band) dispatch({ type: "payload", code, payload: data });
      }).finally(() => pending.current.delete(code));
    }
  }, [selection.codes, selection.payloads, age, dispatch]);
}

function Selected(props: SearchViewProps) {
  const { selection, dispatch, age, setAge } = props;
  usePayloads(props);
  if (!selection.codes.length)
    return <p className="text-sm text-muted">Add up to four codes from the results to compare their salaries.</p>;
  const payloads = selection.codes.map((c) => selection.payloads[c]).filter(Boolean);
  return (
    <section aria-label="Salary chart" className="space-y-3">
      <h2 className="text-lg font-semibold">What each code pays, and the salary floor</h2>
      <div className="flex flex-wrap items-center gap-2">
        {selection.codes.map((code) => (
          <span key={code} className="flex items-center gap-2 rounded-full border border-line bg-panel px-3 py-1 text-sm">
            <span className="font-mono">{code}</span>
            <label className="flex items-center gap-1 text-xs text-muted">
              <input type="checkbox" disabled={!age} checked={!!selection.simulated[code]}
                onChange={() => dispatch({ type: "simulated", code })}
                aria-label={`Simulated bar for ${code}`} />
              simulated
            </label>
            <button type="button" aria-label={`Remove ${code}`} onClick={() => dispatch({ type: "remove", code })}
              className="text-muted hover:text-ink">×</button>
          </span>
        ))}
        <label className="text-sm">
          Age band for simulated bars{" "}
          <select value={age ?? ""} onChange={(e) => setAge((e.target.value || null) as AgeBand | null)}
            className="rounded border border-line bg-panel px-1">
            <option value="">none</option>
            {AGE_BANDS.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
        </label>
      </div>
      {payloads.length > 0 && (
        <SalaryChart payloads={payloads} eligibility={{}} simulated={age ? selection.simulated : {}} />
      )}
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
        <>
          <AdPassages answer={state.answer} />
          <ResultList answer={state.answer} selected={selection.codes}
            onSelect={(code) => dispatch({ type: "add", code })} />
        </>
      )}
      <Selected {...props} />
    </>
  );
}
