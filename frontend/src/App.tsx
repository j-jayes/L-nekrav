import { useEffect, useReducer, useRef, useState } from "react";
import { api, type Registry } from "./api/client";
import { AdvisorDrawer } from "./components/AdvisorDrawer";
import { Notice } from "./components/Notice";
import { type Draft, emptyDraft, offerFrom } from "./lib/offer";
import { initial, select } from "./lib/selection";
import { type AgeBand, parse, type Region, serialise, type View } from "./lib/urlState";
import { LegalView } from "./views/LegalView";
import { NumberView } from "./views/NumberView";
import { SearchView } from "./views/SearchView";

// The page reads as three steps (006 FR-016): find the code, see your number against it, the rules.
const STEPS: { view: View; label: string }[] = [
  { view: "search", label: "1 Find your code" },
  { view: "number", label: "2 Your number" },
  { view: "legal", label: "3 The rules" },
];

/** Whether the screen is wide enough for the drawer to sit beside the page (Tailwind's `lg`). */
const wideQuery = () => (typeof matchMedia === "function" ? matchMedia("(min-width: 1024px)") : null);

function useWide() {
  const [wide, setWide] = useState(() => wideQuery()?.matches ?? false);
  useEffect(() => {
    const query = wideQuery();
    if (!query) return;
    const on = () => setWide(query.matches);
    query.addEventListener("change", on);
    return () => query.removeEventListener("change", on);
  }, []);
  return wide;
}

/** Drop codes the server does not know (a 404 from /occupations/{code}). */
async function known(codes: string[]) {
  const ok = await Promise.all(codes.map(async (code) =>
    (await api.GET("/api/v1/occupations/{code}", { params: { path: { code } } })).response.ok));
  return { valid: codes.filter((_, i) => ok[i]), unknown: codes.filter((_, i) => !ok[i]) };
}

export default function App() {
  const [start] = useState(() => parse(location.search));
  const [view, setView] = useState<View>(start.state.view);
  const [age, setAge] = useState<AgeBand | null>(start.state.age);
  const [region, setRegion] = useState<Region | null>(start.state.region);
  const [selection, dispatch] = useReducer(select, undefined, initial);
  const [loaded, setLoaded] = useState(start.state.codes.length === 0);
  const [draft, setDraft] = useState<Draft>(emptyDraft); // the candidate's number and offer details, memory only
  const offer = offerFrom(draft);
  const [registry, setRegistry] = useState<Registry | null>(null);
  const [advisor, setAdvisor] = useState(false);
  const wide = useWide();
  const trigger = useRef<HTMLButtonElement>(null);
  const closeAdvisor = () => { setAdvisor(false); trigger.current?.focus(); };

  useEffect(() => {
    api.GET("/api/v1/legal/registry").then(({ data }) => data && setRegistry(data));
  }, []);

  useEffect(() => {
    if (loaded) return;
    known(start.state.codes).then(({ valid, unknown }) => {
      dispatch({ type: "load", codes: valid, dropped: [...start.dropped, ...unknown] });
      setLoaded(true);
    });
  }, [loaded, start]);

  useEffect(() => {
    if (loaded) history.replaceState(null, "", serialise({ view, codes: selection.codes, age, region }));
  }, [loaded, view, selection.codes, age, region]);

  return (
    <>
    {/* On wide screens the open drawer sits beside the page; on a phone it covers it, and the page
        is inert until it closes. */}
    <div data-page inert={advisor && !wide} className={`mx-auto max-w-5xl px-4 pb-16 ${advisor ? "lg:mr-[28rem] lg:ml-4" : ""}`}>
      <header className="flex flex-wrap items-baseline justify-between gap-2 py-4">
        <div>
          <h1 className="text-2xl font-bold">Lönekrav</h1>
          <p className="text-sm text-muted">SSYK codes and the salary requirement for Swedish work permits</p>
        </div>
        <button type="button" ref={trigger} onClick={() => (advisor ? closeAdvisor() : setAdvisor(true))} aria-expanded={advisor}
          className="rounded border border-accent px-3 py-1.5 text-sm text-accent">Ask the advisor</button>
      </header>
      <nav aria-label="Steps" className="mb-4 flex gap-1 overflow-x-auto border-b border-line">
        {STEPS.map((t) => (
          <button key={t.view} type="button" onClick={() => setView(t.view)}
            aria-current={view === t.view ? "page" : undefined}
            className={`whitespace-nowrap px-3 py-2 text-sm ${view === t.view ? "border-b-2 border-accent font-semibold" : "text-muted"}`}>
            {t.label}
          </button>
        ))}
      </nav>
      {selection.note && <Notice kind="warn">{selection.note}</Notice>}
      <main className="mt-4 space-y-6">
        {view === "search" && <SearchView selection={selection} dispatch={dispatch} onNext={() => setView("number")} />}
        {view === "number" && (
          <>
            <NumberView selection={selection} dispatch={dispatch} age={age} setAge={setAge} region={region}
              setRegion={setRegion} draft={draft} setDraft={setDraft} onSearch={() => setView("search")}
              rules={registry?.rules} exemptions={Object.values(registry?.exemptions ?? {})} />
            <button type="button" onClick={() => setView("legal")}
              className="rounded border border-accent px-3 py-1.5 text-sm text-accent">Next: the rules →</button>
          </>
        )}
        {view === "legal" && <LegalView registry={registry} draft={draft} onApplied={(d) => setDraft(d)} />}
      </main>
    </div>
    {/* Hidden, not unmounted, when closed: a run keeps going and its answer is still there. */}
    <div hidden={!advisor}>
      <AdvisorDrawer offer={offer} dispatch={dispatch} onClose={closeAdvisor} open={advisor} modal={!wide} />
    </div>
    </>
  );
}
