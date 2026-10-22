// Serve recorded API responses (src/test/fixtures, from scripts/record_api_fixtures.py) to fetch.
import { vi } from "vitest";

export type Fixture = { status: number; body: unknown };
const files = import.meta.glob<{ default: Fixture }>("./fixtures/*.json", { eager: true });

export function fixture(name: string): Fixture {
  const f = files[`./fixtures/${name}.json`];
  if (!f) throw new Error(`no fixture ${name}`);
  return f.default;
}

type Route = Fixture | ((body: unknown, url: URL) => Fixture | Promise<Fixture>);

/** Stub fetch with `{"GET /api/v1/occupations/2512": fixture(...)}`; a key may include the query.
 * Unrouted requests answer 404. Returns the list of requests seen. */
export function serve(routes: Record<string, Route>) {
  const seen: { method: string; url: URL; body: unknown }[] = [];
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const req = input instanceof Request ? input : new Request(new URL(String(input), "http://page"), init);
    const url = new URL(req.url, "http://page");
    const text = req.method === "GET" ? "" : await req.text();
    const body = text ? JSON.parse(text) : undefined;
    seen.push({ method: req.method, url, body });
    const route = routes[`${req.method} ${url.pathname}${url.search}`] ?? routes[`${req.method} ${url.pathname}`];
    const f = typeof route === "function" ? await route(body, url) : route ?? { status: 404, body: { detail: "no route" } };
    return new Response(JSON.stringify(f.body), { status: f.status, headers: { "Content-Type": "application/json" } });
  }));
  return seen;
}
