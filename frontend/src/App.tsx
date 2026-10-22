import { useEffect, useReducer, useState } from "react";
import { api, type Offer, type Registry } from "./api/client";
import { Notice } from "./components/Notice";
import { OfferBox } from "./components/OfferBox";
import { type Draft, emptyDraft } from "./lib/offer";
import { initial, select } from "./lib/selection";
import { type AgeBand, parse, serialise, type View } from "./lib/urlState";
import { CompareView } from "./views/CompareView";
import { LegalView } from "./views/LegalView";
import { SearchView } from "./views/SearchView";

const TABS: { view: View; label: string }[] = [
  { view: "search", label: "Find a code" },
  { view: "compare", label: "Compare" },
  { view: "legal", label: "The rules" },
];

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
  const [selection, dispatch] = useReducer(select, undefined, initial);
  const [loaded, setLoaded] = useState(start.state.codes.length === 0);
  const [draft, setDraft] = useState<Draft>(emptyDraft);
  const [offer, setOffer] = useState<Offer | null>(null);
  const [registry, setRegistry] = useState<Registry | null>(null);

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
    if (loaded) history.replaceState(null, "", serialise({ view, codes: selection.codes, age }));
  }, [loaded, view, selection.codes, age]);

  return (
    <div className="mx-auto max-w-5xl px-4 pb-16">
      <header className="flex flex-wrap items-baseline justify-between gap-2 py-4">
        <div>
          <h1 className="text-2xl font-bold">Lönekrav</h1>
          <p className="text-sm text-muted">SSYK codes and the salary requirement for Swedish work permits</p>
        </div>
      </header>
      <nav aria-label="Views" className="mb-4 flex gap-1 border-b border-line">
        {TABS.map((t) => (
          <button key={t.view} type="button" onClick={() => setView(t.view)}
            aria-current={view === t.view ? "page" : undefined}
            className={`px-3 py-2 text-sm ${view === t.view ? "border-b-2 border-accent font-semibold" : "text-muted"}`}>
            {t.label}
          </button>
        ))}
      </nav>
      {selection.note && <Notice kind="warn">{selection.note}</Notice>}
      <main className="mt-4 space-y-6">
        {view !== "legal" && selection.codes.length > 0 && (
          <OfferBox code={selection.codes[0]} draft={draft} offer={offer} registry={registry}
            onApplied={(d, o) => { setDraft(d); setOffer(o); }} onClear={() => setOffer(null)} />
        )}
        {view === "search" && (
          <SearchView selection={selection} dispatch={dispatch} age={age} setAge={setAge} offer={offer} />
        )}
        {view === "compare" && <CompareView codes={selection.codes} offer={offer} onSearch={() => setView("search")} />}
        {view === "legal" && <LegalView registry={registry} draft={draft} onApplied={(d, o) => { setDraft(d); setOffer(o); }} />}
      </main>
    </div>
  );
}
