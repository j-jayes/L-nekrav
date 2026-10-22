# Implementation Plan: Lönekrav web client and container

**Branch**: `004-web-client-docker` | **Date**: 2026-10-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-web-client-docker/spec.md`

## Summary

Feature 004 adds an English single-page app with three views (search with the salary chart,
compare, and the legal guide with its calculator) and an advisor drawer. The same FastAPI app
serves it at `/`, and the whole stack ships as one self-contained image. The page reads every
figure from the existing API through types generated from its OpenAPI schema, so it holds no
domain logic. The backend changes are small:
- the page is served at `/` and `/assets` (R2);
- the agent card URL becomes configurable, and the host and port come from the environment (R3);
- a read-only `GET /api/v1/legal/registry` serves the legal guide (R9).

## Technical Context

**Language/Version**: Python 3.12 (uv) for the backend; TypeScript 5.9 on Node 22 for the page.

**Primary Dependencies**:
- Backend: unchanged (the 003 stack). `StaticFiles` comes from Starlette, which FastAPI already
  depends on.
- Frontend: Vite 8.3.3, React 19.3.0, Tailwind 4.3.3, openapi-typescript 7.13.0 and openapi-fetch
  0.17.0, and react-markdown 10.1.0 (R1).

**Storage**: none new. The page keeps state in memory and in the query string (R4). The image
carries the Milvus Lite index and `data/processed/` (R10).

**Testing**:
- pytest, offline by default: static serving, the card URL, `/legal/registry` and OpenAPI drift.
- Vitest with Testing Library, on recorded real API responses and captured SSE bytes.
- Playwright with axe against `lonekrav-serve` and against the container (R12).

**Target Platform**:
- Locally: `uv run lonekrav-serve`, with `npm run build` beforehand, or `npm run dev` with a proxy
  to 8000.
- Container: `docker compose up --build` on linux/arm64, on the maintainer's machine.
- Cloud Run (amd64) is documented only.

**Project Type**: a web service plus a single-page web client in one repository.

**Performance Goals**:
- The list updates within 0.5 s of a keystroke (SC-001).
- The full ranking of a 600-word ad appears within 3 s of a pause, warm (SC-002).
- Start-up takes 60 s or less (SC-006).

**Constraints**:
- No figure is computed in the page (FR-007).
- No legal text or amount is hard-coded in the page (Principle II); the legal-literal scan is
  extended to `frontend/src`.
- Container memory stays under 4 GB, and an overrun goes to the maintainer (FR-027).
- The key only arrives at run time (FR-030).
- No request content is logged (unchanged).

**Scale/Scope**: three views, a drawer, about 12 components; one image and one compose service.

## Constitution Check

*GATE: checked before research, and again after design.*

| Principle | How the design complies |
|---|---|
| I. Core first, adapters thin | The page is another adapter. It reads `applicable_rule_id`, eligibility answers and compare columns from core and only maps them to pixels and text (R8). The one new route is a pass-through to `load_registry()` through `Service.registry()`. Types come from the OpenAPI schema (R6). |
| II. Data integrity | Every figure comes from an API payload. A null draws nothing and adds a note. The simulated bar is off by default, marked as simulated, and shows its formula (FR-007, FR-008). Legal text comes from `/legal/registry`. The legal-literal test now also scans `frontend/src`, excluding recorded fixtures. The chart credits SCB and Medlingsinstitutet. |
| III. Honest fit | Results and comparison show `honest_fit` from the payloads. Columns keep the user's order and are never sorted by threshold (FR-012). The drawer shows the memo's footer unchanged. |
| IV. Test first, proven by hand | Each behaviour gets a failing Vitest or pytest first (R12). The evidence covers the Playwright screenshots at two widths, axe, the EN/SV top three, the drawer run, the container's memory and the transcripts in `references/`. |
| V. Compact and portable | One image, one port and one compose service with `mem_limit: 4g`. The models and index are in the image. Without the key, everything works except the advisor. `MILVUS_URI` still switches the store. |
| VI. Simplicity | There is no router, chart library or state library. The URL is the router (R4), and `openapi-fetch` is the client. The new settings are `LONEKRAV_PUBLIC_URL`, `HOST` and `PORT`, which the spec and Cloud Run need. |

Result: pass. Complexity Tracking lists one judgement call.

## Project Structure

### Documentation (this feature)

```text
specs/004-web-client-docker/
├── plan.md  research.md  data-model.md  quickstart.md
├── contracts/http.md  contracts/ui.md  contracts/a2a-client.md
├── checklists/requirements.md
└── tasks.md            # /speckit-tasks
```

### Source Code (repository root)

```text
src/lonekrav/
├── app.py                    # create_app(..., frontend_dist=FRONTEND_DIST): GET / + /assets before the MCP mount; main() reads HOST, PORT
├── api/v1.py                 # + GET /legal/registry
├── core/service.py           # + Service.registry()
└── protocols/a2a_server.py   # card(base_url); add_a2a reads LONEKRAV_PUBLIC_URL
frontend/
├── package.json  package-lock.json  vite.config.ts  tsconfig.json  index.html  playwright.config.ts
├── src/
│   ├── main.tsx  App.tsx  index.css          # App: view switch from URL state, drawer
│   ├── api/openapi.json  schema.d.ts  client.ts   # generated + one openapi-fetch client (R6)
│   ├── lib/
│   │   ├── a2aClient.ts      # SSE over fetch, SendStreamingMessage, CancelTask (R7)
│   │   ├── urlState.ts       # parse/serialise view, codes, age (R4)
│   │   ├── searchSession.ts  # two speeds, latest-text-wins (R5)
│   │   ├── selection.ts      # reducer: add/remove/advisor-select, limits
│   │   └── chartScale.ts     # value -> x, ticks (R8)
│   ├── views/SearchView.tsx  CompareView.tsx  LegalView.tsx
│   ├── components/
│   │   ├── SalaryChart.tsx  ChartTable.tsx  ScoreStrip.tsx  AdPassages.tsx  ResultList.tsx
│   │   ├── OfferForm.tsx  EligibilityResult.tsx  SourceLink.tsx  AdvisorDrawer.tsx  Notice.tsx
│   └── test/fixtures/        # recorded API responses and SSE bytes (R12)
└── e2e/views.spec.ts  e2e/ad-languages.spec.ts  e2e/advisor.spec.ts
docker/Dockerfile  docker-compose.yml  .dockerignore
scripts/
├── export_openapi.py  fetch_models.py  record_api_fixtures.py
├── serve_fake_advisor.py  container_memory.py
tests/
├── integration/test_frontend_serving.py  test_openapi_drift.py
├── integration/test_api.py  (+ /legal/registry)  test_a2a.py  (+ card URL)
└── unit/test_legal.py  (literal scan extended to frontend/src)
references/
├── a2a-sse-wire.md  container-memory.md  web-client-screenshots/  web-client-e2e.md
README.md                     # local run, env vars, Cloud Run variant (not deployed)
```

**Structure Decision**: `frontend/` sits at the repository root, as the development plan's layout
has it. Its tests live beside the code (`*.test.ts(x)`) and in `frontend/e2e/`. The backend keeps
its layout.

## Design notes

- **App wiring order**: the REST router, then the A2A routes, then `GET /` and `/assets` when the
  build exists, then the MCP root mount, which stays last.
- **Views**:
  - `?view=search` is the default. It holds the search box, the result list with passages and the
    score strip, the selection chips, the chart, and the age band and simulated toggles.
  - `?view=compare` holds the columns for the selected codes and the offer form.
  - `?view=legal` holds the guide, the timeline and the calculator.
  - The drawer is available on every view.
- **The offer** is one draft shared by compare, the calculator, the chart's floor line and the
  drawer. It lives only in memory.
- **Advisor → chart**:
  - A `ui_sync:get_occupation_salary` artifact selects `result.code` and stores `result` as that
    code's payload.
  - A `ui_sync:compare_occupations` artifact selects `result.columns[].code`.
  - A `ui_sync:search_occupations` artifact shows its hits but selects nothing.
  - Selections past four keep the most recent four, and the drawer says which codes were left out.
- **Score strip**: one cell per method in `hit.ranks` (kblab, bm25, harrier), showing the rank, or
  "not run" for `null`.
- **The accessibility table** and the chart share one data mapping, so they cannot disagree.

## Complexity Tracking

| Judgement call | Why | Simpler alternative rejected because |
|---|---|---|
| A new REST route, `/legal/registry`, with no MCP twin | The legal guide needs the code lists and statements, which only the registry has (R9) | Hard-coding them in the page breaks Principle II. Adding an MCP tool nobody asked for breaks Principle VI. |
