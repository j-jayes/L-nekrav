import { type Dispatch, useEffect, useRef, useState } from "react";
import Markdown from "react-markdown";
import type { Comparison, Offer, SalaryPayload } from "../api/client";
import { type AdvisorEvent, type AdvisorInput, agentCard, cancelTask, sendMessage } from "../lib/a2aClient";
import type { Action } from "../lib/selection";
import { Notice } from "./Notice";

type Run = {
  state: "idle" | "running" | "completed" | "failed" | "rejected" | "canceled" | "lost";
  taskId: string | null;
  progress: string[];
  memo: string | null;
  error: string | null;
  selected: string[]; // codes the advisor selected on the chart
};
const IDLE: Run = { state: "idle", taskId: null, progress: [], memo: null, error: null, selected: [] };

// Shown before the first send whatever happens to the agent card request (FR-019); the card's own
// description replaces it once read.
const FALLBACK_NOTICE = "Your ad, background and offer go to a third-party language model (via OpenRouter) "
  + "when you ask.";

const ENDED: Record<string, string> = {
  rejected: "The advisor is unavailable",
  failed: "The run failed",
  lost: "The connection was lost",
  canceled: "The run was cancelled.",
};

type Props = {
  offer: Offer | null;
  dispatch: Dispatch<Action>;
  onClose: () => void;
  open?: boolean; // focus moves into the drawer when it opens
  modal?: boolean; // full-screen at phone width: a modal dialog over an inert page
};

/** Ask lonekrav-advisor (US5): progress streams in, the codes it looks up are selected on the
 * chart, and its memo is shown with its footer. Nothing typed here is stored (FR-024). */
export function AdvisorDrawer({ offer, dispatch, onClose, open = true, modal = false }: Props) {
  const [notice, setNotice] = useState<string | null>(null);
  const [ad, setAd] = useState("");
  const [background, setBackground] = useState("");
  const [withOffer, setWithOffer] = useState(false);
  const [run, setRun] = useState<Run>(IDLE);
  const abort = useRef<AbortController | null>(null);
  const first = useRef<HTMLTextAreaElement>(null);
  const running = run.state === "running";

  useEffect(() => {
    if (open) first.current?.focus();
  }, [open]);

  useEffect(() => {
    agentCard().then((card) => setNotice(card?.description ?? null)).catch(() => setNotice(null));
  }, []);

  function onEvent(e: AdvisorEvent) {
    if (e.type === "task") setRun((r) => ({ ...r, taskId: e.taskId }));
    else if (e.type === "status" && e.state === "working" && e.text)
      setRun((r) => ({ ...r, progress: [...r.progress, e.text] }));
    else if (e.type === "status" && e.state !== "working" && e.state !== "submitted")
      setRun((r) => ({ ...r, state: e.state as Run["state"], error: e.state === "completed" ? null : e.text }));
    else if (e.type === "ui_sync" && e.tool === "get_occupation_salary") {
      // Select the code only: the chart fetches its own payload for the age band on screen.
      const payload = e.result as SalaryPayload;
      dispatch({ type: "advisor", codes: [payload.code] });
      setRun((r) => ({ ...r, selected: [...new Set([...r.selected, payload.code])] }));
    } else if (e.type === "ui_sync" && e.tool === "compare_occupations") {
      const codes = (e.result as Comparison).columns.map((c) => c.code);
      dispatch({ type: "advisor", codes });
      setRun((r) => ({ ...r, selected: [...new Set([...r.selected, ...codes])] }));
    } else if (e.type === "memo") setRun((r) => ({ ...r, memo: e.markdown }));
    else if (e.type === "error") setRun((r) => ({ ...r, state: e.state, error: e.message }));
  }

  async function ask() {
    if (running || !ad.trim()) return;
    const input: AdvisorInput = { ad, ...(background.trim() ? { background } : {}),
      ...(withOffer && offer ? { offer } : {}) };
    abort.current = new AbortController();
    setRun({ ...IDLE, state: "running" });
    for await (const e of sendMessage(input, { signal: abort.current.signal })) onEvent(e);
  }

  async function cancel() {
    const id = run.taskId;
    abort.current?.abort();
    if (id) await cancelTask(id).catch(() => null);
    setRun((r) => ({ ...r, state: "canceled", error: null }));
  }

  return (
    <aside aria-label="Advisor" role={modal ? "dialog" : undefined} aria-modal={modal || undefined}
      onKeyDown={(e) => e.key === "Escape" && onClose()} className="fixed inset-y-0 right-0 z-10 flex w-full max-w-md flex-col gap-3 overflow-y-auto border-l border-line bg-page p-4 shadow-xl">
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg font-semibold">Ask the advisor</h2>
        <button type="button" onClick={onClose} className="text-sm text-accent underline">Close</button>
      </div>
      <p className="text-sm text-muted">{notice ?? FALLBACK_NOTICE}</p>
      <form className="space-y-2" onSubmit={(e) => { e.preventDefault(); void ask(); }}>
        <label htmlFor="adv-ad" className="block text-sm">Job ad</label>
        <textarea id="adv-ad" ref={first} rows={6} value={ad} onChange={(e) => setAd(e.target.value)}
          className="w-full rounded border border-line bg-panel p-2" />
        <label htmlFor="adv-bg" className="block text-sm">Your background <span className="text-muted">(optional)</span></label>
        <textarea id="adv-bg" rows={2} value={background} onChange={(e) => setBackground(e.target.value)}
          className="w-full rounded border border-line bg-panel p-2" />
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={withOffer} disabled={!offer} onChange={(e) => setWithOffer(e.target.checked)} />
          Include my offer {!offer && <span className="text-muted">(type your number in step 2 first)</span>}
        </label>
        <div className="flex gap-2">
          <button type="submit" disabled={running || !ad.trim()}
            className="rounded bg-accent px-3 py-1.5 text-sm text-white disabled:opacity-50">Ask</button>
          {running && <button type="button" onClick={() => void cancel()} className="text-sm text-accent underline">Cancel</button>}
        </div>
        {running && <p className="text-xs text-muted">A request is running: wait for it, or cancel it to ask again.</p>}
      </form>
      {run.progress.length > 0 && (
        <ul aria-label="Progress" aria-live="polite" className="space-y-0.5 text-sm text-muted">
          {run.progress.map((p, i) => <li key={i}>{p}</li>)}
        </ul>
      )}
      {run.selected.length > 0 && (
        <p className="text-sm">Selected on the chart by the advisor: {run.selected.join(", ")}</p>
      )}
      {ENDED[run.state] && (
        <Notice kind={run.state === "canceled" ? "info" : "error"}>
          {ENDED[run.state]}{run.error && `: ${run.error}`}{" "}
          <button type="button" className="text-accent underline" onClick={() => void ask()}>Try again</button>
        </Notice>
      )}
      {run.memo && (
        <section aria-label="Memo" className="prose-sm space-y-2 rounded border border-line bg-panel p-3 text-sm [&_h2]:font-semibold [&_h3]:font-semibold [&_ul]:list-disc [&_ul]:pl-5">
          <Markdown>{run.memo}</Markdown>
        </section>
      )}
    </aside>
  );
}
