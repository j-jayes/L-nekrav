// The page's state in the address: view, selected codes and age band (contracts/ui.md, R4).
// The ad, background and offer are never written here (FR-024).

export const VIEWS = ["search", "compare", "legal"] as const;
export type View = (typeof VIEWS)[number];
// SCB's age bands in TAB5844, as core.salary.AGE_BANDS_ names them.
export const AGE_BANDS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65-68"] as const;
export type AgeBand = (typeof AGE_BANDS)[number];
export const MAX_CODES = 4;

export type PageState = { view: View; codes: string[]; age: AgeBand | null };

const isView = (v: string | null): v is View => VIEWS.includes(v as View);
const isAge = (v: string | null): v is AgeBand => AGE_BANDS.includes(v as AgeBand);

/** Read the address. `dropped` lists codes that were malformed, repeated or past the limit. */
export function parse(search: string): { state: PageState; dropped: string[] } {
  const q = new URLSearchParams(search);
  const codes: string[] = [];
  const dropped: string[] = [];
  for (const c of (q.get("codes") ?? "").split(",").filter(Boolean)) {
    if (/^\d{4}$/.test(c) && !codes.includes(c) && codes.length < MAX_CODES) codes.push(c);
    else dropped.push(c);
  }
  const view = q.get("view");
  const age = q.get("age");
  return { state: { view: isView(view) ? view : "search", codes, age: isAge(age) ? age : null }, dropped };
}

export function serialise(s: PageState): string {
  const q = new URLSearchParams({ view: s.view });
  if (s.codes.length) q.set("codes", s.codes.join(","));
  if (s.age) q.set("age", s.age);
  return `?${q}`;
}
