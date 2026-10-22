// Two-speed search (research R5): fast on every change, accurate (full) after a pause.
// Only an answer for the text still in the box is shown, and a full answer is never replaced by
// a fast one for the same text.
import { api, type SearchAnswer } from "../api/client";
import type { components } from "../api/schema";

export const PAUSE_MS = 600;
export const MAX_TEXT = 20_000; // SearchRequest.text max_length
type SearchRequest = components["schemas"]["SearchRequest"];
export type SearchFn = (req: SearchRequest, signal: AbortSignal) => Promise<SearchAnswer>;

export type SessionState = {
  text: string;
  answer: SearchAnswer | null;
  shown: "fast" | "full" | null;
  refining: boolean; // a full search is waiting or running
  error: string | null;
};

/** A pasted ad (several lines, or more than 40 words) is searched by its job-describing parts. */
export const wantsParseAd = (text: string) =>
  text.split("\n").filter((l) => l.trim()).length > 1 || text.trim().split(/\s+/).length > 40;

export const apiSearch: SearchFn = async (body, signal) => {
  const { data, error } = await api.POST("/api/v1/search", { body, signal });
  if (error || !data) throw new Error(JSON.stringify(error));
  return data;
};

const aborted = (e: unknown) => e instanceof DOMException && e.name === "AbortError";

export class SearchSession {
  private state: SessionState = { text: "", answer: null, shown: null, refining: false, error: null };
  private fast?: AbortController;
  private full?: AbortController;
  private timer?: ReturnType<typeof setTimeout>;
  private fullFor: string | null = null; // the text the shown full answer was for

  constructor(private search: SearchFn, private onChange: (s: SessionState) => void) {}

  private set(patch: Partial<SessionState>) {
    this.state = { ...this.state, ...patch };
    this.onChange(this.state);
  }

  setText(text: string) {
    this.fast?.abort();
    this.full?.abort();
    clearTimeout(this.timer);
    if (!text.trim()) return this.set({ text, answer: null, shown: null, refining: false, error: null });
    if (text.length > MAX_TEXT)
      return this.set({ text, refining: false, error: "The text is too long: the limit is 20 000 characters." });
    this.set({ text, refining: true, error: null });
    this.fast = this.send(text, "fast");
    this.timer = setTimeout(() => (this.full = this.send(text, "full")), PAUSE_MS);
  }

  private send(text: string, mode: "fast" | "full") {
    const ctl = new AbortController();
    this.search({ text, mode, k: 5, parse_ad: wantsParseAd(text) }, ctl.signal).then(
      (answer) => {
        if (text !== this.state.text || (mode === "fast" && this.fullFor === text)) return;
        this.fullFor = mode === "full" ? text : null;
        this.set({ answer, shown: mode, refining: mode === "fast" ? this.state.refining : false });
      },
      (e) => {
        if (aborted(e) || text !== this.state.text) return;
        this.set({ error: "The search failed; showing the previous results.", refining: false });
      },
    );
    return ctl;
  }
}
