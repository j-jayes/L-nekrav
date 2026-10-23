# Research: Lönekrav web client and container

Each entry gives a decision, the reason for it, and the alternatives rejected. Versions were checked
on npm and PyPI on 2026-10-22. Every pinned npm version is at least two weeks old.

## R1. Frontend stack and versions

**Decision**: Vite 8.3.3 with `@vitejs/plugin-react` 6.1.2, React 19.3.0 and React DOM 19.3.0,
TypeScript 5.9.3, Tailwind 4.3.3 with `@tailwindcss/vite` 4.3.3, `openapi-typescript` 7.13.0 and
`openapi-fetch` 0.17.0, `react-markdown` 10.1.0. For tests: Vitest 5.0.3, jsdom 30.1.2,
`@testing-library/react` 16.3.3 and `@testing-library/dom` 10, `@playwright/test` 1.64.0 and
`@axe-core/playwright` 4.13.0. Node 22 (22.22.0 is installed locally; the image uses `node:22-slim`).
`package-lock.json` is committed, the build uses `npm ci`, and versions are exact (no `^`).

**Rationale**: these are the stack the constitution names. TypeScript stays on 5.9 because
openapi-typescript 7.13 declares `typescript: ^5.x`. React 19.3.1, Vite 8.3.5, Vitest 5.0.5,
jsdom 30.1.3, Playwright 1.64.1 and axe 4.14.0 are each less than two weeks old, so the pins are
one release back.

**Alternatives**: TypeScript 7.0 (the native compiler) is outside openapi-typescript's peer range.
A charting library is rejected because the development plan asks for hand-written SVG, and the
chart has five custom mark types. A router library is rejected because the views are a query
parameter (R4).

## R2. Serving the page from the FastAPI app, next to a root MCP mount

**Decision**: `create_app(frontend_dist=FRONTEND_DIST)`, where the default `FRONTEND_DIST` is
`frontend/dist`. When `index.html` exists there, the app registers two things:
- `GET /`, which returns `index.html`;
- `app.mount("/assets", StaticFiles(...))`.

Both are registered before the MCP root mount, which stays last (003 R2). When there is no build,
`GET /` returns 404 with a detail saying that the frontend is not built and how to build it, and
the rest of the app is unchanged.

**Rationale**: the MCP app is mounted at `/`, so it catches every path registered after it, and an
SPA catch-all route registered before it would steal `GET /mcp`. The page keeps all its state in
the query string (R4), so it needs only `/` and `/assets/*`, and no catch-all at all. Vite emits
hashed files under `assets/`. Files in `public/` are not used.

**Alternatives**: `StaticFiles(html=True)` mounted at `/` would conflict with the MCP mount. A
catch-all route that excludes `/mcp` would put routing rules in two places.

## R3. The agent card's public address, host and port

**Decision**: `LONEKRAV_PUBLIC_URL` (default `http://localhost:8000`) is the base of the card's
interface URL, which is `{base}/a2a` with any trailing slash removed. `a2a_server.card(base)`
builds the card, and `add_a2a` reads the setting once, when the app is created. `main()` reads
`HOST` (default `127.0.0.1`) and `PORT` (default `8000`). The image sets `HOST=0.0.0.0`; Cloud Run
supplies `PORT`.

**Rationale**: FR-028 asks for exactly this. `PORT` is the name Cloud Run injects, so the README's
Cloud Run section needs no extra setting. Locally nothing changes.

**Alternatives**: deriving the URL from each request's `Host` header is wrong behind a proxy that
rewrites it, and the a2a-sdk card route serves a fixed card.

## R4. Page state in the address

**Decision**: the query string is `?view=search|compare|legal&codes=2512,2514&age=25-34`, read once
on load and written with `history.replaceState` on every change. Unknown codes (checked against
`GET /api/v1/occupations/{code}`, so a 404 drops the code) and codes past the limit are dropped,
with a note. The ad, background and offer are never written to it (FR-024, FR-032).

**Rationale**: a reload or a shared link restores the selection (clarification 3). `replaceState`
keeps the back button from filling up with one entry per selection.

**Alternatives**: hash routing works the same way but reads less cleanly. A router library is not
needed for three views.

## R5. Search while typing: two speeds, and the latest answer wins

**Decision**:
- Every input change sends a fast search right away, with an `AbortController` that cancels the
  one still in flight.
- After 600 ms without typing, the page sends a full search.
- Each request carries the text it was sent for, and an answer is shown only if that text is still
  in the box (FR-002).
- `parse_ad` is on when the text has more than one non-empty line or more than 40 words. A typed
  title is searched as it is; a pasted ad uses ad parsing in both modes.
- The full answer replaces the fast one. A fast answer never replaces a full answer for the same
  text.

**Rationale**: fast search is 40–63 ms p95 on the server (002), which meets SC-001's 0.5 s with
room for the round trip. The 600 ms pause is long enough not to fire mid-word, and short enough
for SC-002's 3 s target, because a full search of a 600-word ad with `parse_ad` takes about 1 s
warm (003 transcript). The line or word test is the simplest rule that tells a title from an ad.
The API already reports `passages` and `title_list` when `parse_ad` is on.

**Alternatives**: debouncing the fast search too adds delay that typing does not need. A streaming
search endpoint would need new server work, and two requests already give the "Harrier arrives on
pause" behaviour.

## R6. Typed API client

**Decision**: `scripts/export_openapi.py` writes `create_app().openapi()` to
`frontend/src/api/openapi.json` without starting the lifespan, so it loads no models.
`npm run gen` runs `openapi-typescript` to produce `frontend/src/api/schema.d.ts`, and both files are
committed. `frontend/src/api/client.ts` is a single `openapi-fetch` client with `baseUrl: ""`. A
pytest checks that the committed `openapi.json` equals `create_app().openapi()`, so an API change
without a regeneration fails the Python suite. `npm run build` runs `tsc --noEmit` first, so a
field change breaks the build (FR-025).

**Rationale**: the schema is the contract, and generating from it keeps one source of truth
(Principle I's "a new field is added once"). Committing the generated files means the Docker build
needs no running server.

**Alternatives**: generating inside the Docker build needs Python and the app in the node stage.
Hand-written types drift.

## R7. A2A client in the browser

**Decision**: `frontend/src/lib/a2aClient.ts` sends `fetch` POSTs to `/a2a` with the headers
`Content-Type: application/json`, `Accept: text/event-stream` and `A2A-Version: 1.0`, and a JSON-RPC
body with method `SendStreamingMessage` and one data part `{ad, background?, offer?}`. It reads the
response body as a stream, splits it into SSE events at blank lines, and JSON-parses each `data:`
line into a JSON-RPC response whose result is a stream response (task, status update or artifact
update). It yields typed events until the task reaches a final state. Cancelling calls
`CancelTask` with the task id and aborts the fetch. Before writing the parser, the exact bytes on
the wire are captured with `curl -N` against the running server and saved to
`references/a2a-sse-wire.md`. The parser's tests replay those bytes.

**Rationale**: `EventSource` supports only GET, and A2A streaming is a POST. Parsing the real
captured bytes avoids guessing the protobuf-JSON field names (camelCase, `TASK_STATE_*` enums,
`statusUpdate` against `artifactUpdate`). The card is read once, to show whether the advisor is
available and its third-party notice.

**Alternatives**: the a2a JS SDK would add a dependency for one method and one parser, and its v1.0
support is not verified.

## R8. Chart from the payload, with no client-side figures

**Decision**: `SalaryChart.tsx` is hand-written SVG, one row per code:
- a P10–P90 bar, with the P10–P25 band shaded and a median tick;
- age-band mean dots;
- an optional simulated ghost bar (dashed outline, lighter fill, labelled "simulated");
- a vertical floor line for that code.

The floor line is `thresholds` filtered by `applicable_rule_id` from the salary payload. When an
offer is entered, it is the eligibility answer's `rule_id` and `threshold_sek` for that code
instead. A `null` value draws nothing and adds a note. The x scale starts at 0 SEK and covers the
largest P90 and threshold, rounded up to a 10 000 SEK tick. The `dataviz` skill is loaded before the
first chart code, and `viz-distributions` is followed for the bar and band encoding. A `<table>`
with the same figures sits under the chart, visually hidden but available to screen readers, with
a "show as table" toggle (FR-010).

**Rationale**: core already decides which rule applies (`applicable_rule_id`) and returns every
figure, so the page only maps numbers to pixels (FR-007, Principle I). A zero baseline keeps bar
lengths honest.

**Alternatives**: choosing the rule in the client would duplicate a legal rule. A log scale or a
non-zero baseline would distort the comparison.

## R9. The legal guide's data

**Decision**: add `GET /api/v1/legal/registry`, which returns the `Registry` model (medians, rules,
code lists with titles, personal exemptions, statements, each with its source and checked-on
date). It goes through `Service.registry()`. The guide renders it with the existing
`GET /legal/timeline`. MCP does not get a new tool: the timeline resource already covers what a
chat model needs, and the spec does not ask for one.

**Rationale**: FR-013 needs the exempt and banned code lists, the transition rule and the
statements. The timeline carries only counts and summaries, and hard-coding them in the page would
put legal text outside the registry (Principle II).

**Alternatives**: several smaller endpoints (exempt codes, statements) for one page.

## R10. Container image

**Decision**: a multi-stage `docker/Dockerfile`:
1. `node:22-slim`: `npm ci`, then `npm run build`, which produces `frontend/dist`.
2. `python:3.12-slim`, with `uv` copied from `ghcr.io/astral-sh/uv:0.9.9`. It runs
   `uv sync --frozen --no-dev`. Then `scripts/fetch_models.py` downloads both models at the
   revisions pinned in `core/embeddings.SPECS` into `HF_HOME=/models`. Then it copies
   `data/lonekrav_milvus.db` and `data/processed/`, and `frontend/dist` from stage 1.
   - It sets `HF_HUB_OFFLINE=1`, `HOST=0.0.0.0` and `PYTHONUNBUFFERED=1`.
   - It runs as a non-root user, with `CMD ["lonekrav-serve"]`.

`docker-compose.yml` defines one service on port 8000 with `mem_limit: 5g` (4g until measurement, R11). Its environment is
`OPENROUTER_KEY`, `LONEKRAV_LLM_MODEL` and `LONEKRAV_PUBLIC_URL`, interpolated from the shell or
`.env`, so the key reaches the container only at run time (FR-030). A `.dockerignore` keeps out
`.env`, `data/raw/`, `.venv/`, `frontend/node_modules/`, `.git/` and `reports/`.

**Rationale**: clarification 1 asks for a self-contained image. With `HF_HUB_OFFLINE`, a missing
model fails at start-up instead of downloading. The image is built for the host architecture
(arm64 here). torch 2.14.1's PyPI wheels for linux/aarch64 are CPU-only. The linux/x86_64 wheel
pulls in CUDA libraries, so the README's Cloud Run section notes that an amd64 build should use the
CPU wheel index.

**Alternatives**: volumes for models or the index (rejected in clarification 1). Building the
index inside the image takes over an hour and needs the raw data.

**Risk**: the index directory is the Milvus Lite file, and Milvus Lite locks it. The image runs one
process, so this is fine, but `docker compose up` while a local `lonekrav-serve` runs is also fine,
because the container has its own copy.

## R11. Memory measurement

**Decision**: `scripts/container_memory.py` samples `docker stats --no-stream` once a second while
it sends, in turn, a fast search, a full search with a pasted ad (which loads the accurate model),
an eligibility check and a compare. It writes the peak and a per-step table to
`references/container-memory.md`. If the peak is at or above the cap, the work stops and the numbers
go to the maintainer (clarification 2).

**Rationale**: the 001 measurements (KBLab about 1 GB, Harrier about 2.6 GB peak RSS) add up to
about 3.6 GB, close to the cap. The measurement has to come from the real container under the real
`mem_limit`.

**Outcome (2026-10-22)**: under the 4 GB cap the container sat at 3.98 GiB, with 4.23 GB of anon
memory and 3 825 `memory.max` events: swap absorbed it, and nothing was OOM-killed. Uncapped, it
measured 4.20 GiB steady and a 4.54 GiB cgroup peak once Harrier had loaded. The maintainer raised
the cap to 5 GB (`references/container-memory.md`).

## R12. Testing strategy

**Decision**:
- **Python (pytest, offline)**: static serving with a temporary `dist` (index, assets, 404 without a
  build, `/mcp` still answers); the card URL from `LONEKRAV_PUBLIC_URL`; `/legal/registry` against
  the registry; the OpenAPI drift test (R6); `HOST`/`PORT` in `main()`.
- **Frontend unit (Vitest + Testing Library)**:
  - the SSE parser replaying the captured wire bytes;
  - URL state round-trips and the dropping of bad codes;
  - the search session's "only the current text" rule, with fake fetch timings;
  - the selection reducer's four-code limit and the advisor's updates;
  - chart geometry (each mark's position equals its payload value on the scale, a null draws
    nothing, the floor follows `applicable_rule_id` or the eligibility answer);
  - each view against recorded API responses.
- **End to end (Playwright, against `lonekrav-serve` with the real index)**:
  - screenshots of the three views at 390 and 1280 px, with a no-horizontal-scroll check;
  - axe on each view, with no serious or critical violations (SC-009);
  - the English and Swedish ad giving the same top three codes (SC-003);
  - the drawer selecting codes on the chart, using a fake advisor, by starting the server with a
    scripted fake model (`scripts/serve_fake_advisor.py`);
  - one live run with the key, recorded as evidence (SC-008).

Recorded API responses for the unit tests are produced by `scripts/record_api_fixtures.py` from the
running server and committed under `frontend/src/test/fixtures/`, so the frontend tests use real
payloads (the fixture rule from 001).

**Rationale**: the constitution asks for red/green tests, and for proof by hand that a browser
renders. Recording real responses follows the project's "real slices, not hand-written fixtures"
rule. A fake-model server makes the drawer test deterministic and free.
