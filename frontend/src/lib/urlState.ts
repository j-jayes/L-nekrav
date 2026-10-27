// The page's state in the address: view, selected codes, age band and area (contracts/ui.md, R4;
// 006 FR-018). The ad, background, offer and the candidate's number are never written here.

export const VIEWS = ["search", "number", "legal"] as const;
export type View = (typeof VIEWS)[number];
// SCB's age bands in TAB5844, as core.salary.AGE_BANDS_ names them.
export const AGE_BANDS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65-68"] as const;
export type AgeBand = (typeof AGE_BANDS)[number];
export const MAX_CODES = 4;
// SCB's eight national areas (riksområden) in TAB5696, as core.salary.REGIONS names them.
export const REGIONS = {
  SE11: "Stockholm", SE12: "East-Central Sweden", SE21: "Småland and islands", SE22: "South Sweden",
  SE23: "West Sweden", SE31: "North-Central Sweden", SE32: "Central Norrland", SE33: "Upper Norrland",
} as const;
export type Region = keyof typeof REGIONS;

export type PageState = { view: View; codes: string[]; age: AgeBand | null; region: Region | null };

const isView = (v: string | null): v is View => VIEWS.includes(v as View);
const isAge = (v: string | null): v is AgeBand => AGE_BANDS.includes(v as AgeBand);
const isRegion = (v: string | null): v is Region => v != null && Object.hasOwn(REGIONS, v);

/** Read the address. `dropped` lists codes that were malformed, repeated or past the limit. */
export function parse(search: string): { state: PageState; dropped: string[] } {
  const q = new URLSearchParams(search);
  const codes: string[] = [];
  const dropped: string[] = [];
  for (const c of (q.get("codes") ?? "").split(",").filter(Boolean)) {
    if (/^\d{4}$/.test(c) && !codes.includes(c) && codes.length < MAX_CODES) codes.push(c);
    else dropped.push(c);
  }
  const view = q.get("view") === "compare" ? "number" : q.get("view"); // 005 links named the compare view
  const age = q.get("age");
  const region = q.get("region");
  return { state: { view: isView(view) ? view : "search", codes, age: isAge(age) ? age : null,
    region: isRegion(region) ? region : null }, dropped };
}

export function serialise(s: PageState): string {
  const q = new URLSearchParams({ view: s.view });
  if (s.codes.length) q.set("codes", s.codes.join(","));
  if (s.age) q.set("age", s.age);
  if (s.region) q.set("region", s.region);
  return `?${q}`;
}
