---
description: "Task list for Feature 004: Lönekrav web client and container"
---

# Tasks: Lönekrav web client and container

**Input**: `specs/004-web-client-docker/` (spec.md, plan.md, research.md, data-model.md,
contracts/http.md, contracts/ui.md, contracts/a2a-client.md, quickstart.md, checklists/)

**Tests**: required. Constitution Principle IV mandates red/green TDD: run each test task and see it
fail for the stated reason before its implementation task. Python tests use the offline fixtures
from `tests/conftest.py`. Frontend unit tests use responses recorded from the real server
(T011) and the captured SSE bytes (T012), never hand-written payloads.

**Legal literals**: no amount, percentage or legal date in page code or copy. Legal text comes from
`/legal/registry`, and the scan in `tests/unit/test_legal.py` covers `frontend/src` from T010 on.

**Commands**: the frontend runs from `frontend/` (`npm test`, `npm run build`, `npx playwright
test`). Stop `lonekrav-serve` before running the benchmark or a script against the same index.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1–US6 from spec.md

---

## Phase 1: Setup

- [ ] T001 Scaffold `frontend/` by hand, with no template generator. Add `package.json` with the exact versions from research R1 and the scripts `dev`, `build` (`tsc --noEmit && vite build`), `test` (`vitest run`), `gen` (`openapi-typescript src/api/openapi.json -o src/api/schema.d.ts`) and `e2e` (`playwright test`). Add `tsconfig.json` (strict), `vite.config.ts` (React and Tailwind plugins, a dev proxy for `/api`, `/a2a`, `/mcp` and `/.well-known` to `http://localhost:8000`, Vitest with jsdom), `index.html`, `src/main.tsx`, `src/App.tsx` (an empty shell) and `src/index.css` (`@import "tailwindcss"`). Run `npm install` to create `package-lock.json`, then `npm ci && npm run build && npm test -- --passWithNoTests`, all green
- [ ] T002 [P] Add `frontend/playwright.config.ts`. It sets `baseURL` from `BASE_URL` (default `http://localhost:8000`) and has two projects: `phone` (390×844) and `desktop` (1280×800). Run `npx playwright install chromium`
- [ ] T003 [P] Record the baseline: `rtk proxy uv run pytest -q` reports 340 passed

---

## Phase 2: Foundational (blocks every story)

### Backend: serving, settings, registry, schema

- [ ] T004 [P] Write the test `tests/integration/test_frontend_serving.py`, using `create_app(..., frontend_dist=tmp_path)` with a fake `index.html` and `assets/app.js`:
  - `GET /` and `GET /?view=compare&codes=2512` return the index.
  - `GET /assets/app.js` returns 200, and an unknown asset returns 404.
  - With no build, `GET /` returns 404 with the "frontend not built" detail.
  - `POST /mcp` initialize still answers, and `/api/v1/health` is unchanged, with and without a build.
  
  It must fail first (contracts/http.md)
- [ ] T005 Implement `create_app(frontend_dist=FRONTEND_DIST)` in `src/lonekrav/app.py`: `GET /` and the `/assets` `StaticFiles` mount, registered before the MCP root mount (R2). T004 passes
- [ ] T006 [P] Write tests in `tests/integration/test_a2a.py`:
  - with `LONEKRAV_PUBLIC_URL=https://x.test/` (monkeypatched), the card's `supportedInterfaces[0].url` is `https://x.test/a2a`;
  - with it unset, the URL is `http://localhost:8000/a2a`.
  
  Add a test in `tests/unit/test_app_main.py` that `main()` passes `HOST` and `PORT` to `uvicorn.run`, by monkeypatching `uvicorn.run` (R3). Both must fail first
- [ ] T007 Implement `card(base_url)` in `src/lonekrav/protocols/a2a_server.py`, with `add_a2a` reading `LONEKRAV_PUBLIC_URL`. Make `main()` in `src/lonekrav/app.py` read `HOST` and `PORT`. T006 passes
- [ ] T008 [P] Write tests for `GET /api/v1/legal/registry` in `tests/integration/test_api.py` and `Service.registry()` in `tests/unit/test_service.py`. The JSON equals `load_registry().model_dump(mode="json")`, and every row has a source with `checked_on`. They must fail first (R9)
- [ ] T009 Implement `Service.registry()` in `src/lonekrav/core/service.py` and the route in `src/lonekrav/api/v1.py`. T008 passes
- [ ] T010 [P] Extend the literal scan in `tests/unit/test_legal.py` to `frontend/src/**/*.{ts,tsx,css}`, excluding `src/test/fixtures/` and the generated `src/api/`. Plant a literal to see it fail, then remove the plant
- [ ] T011 Write `scripts/export_openapi.py`, which writes `create_app().openapi()` without the lifespan to `frontend/src/api/openapi.json`, and `tests/integration/test_openapi_drift.py`, which fails while the file is missing or stale. Run the export and `npm run gen`. Write `frontend/src/api/client.ts` (`createClient<paths>({baseUrl: ""})`) and commit the generated `openapi.json` and `schema.d.ts` (R6)
- [ ] T012 Write `scripts/record_api_fixtures.py`, which runs against a live `lonekrav-serve` and writes real responses to `frontend/src/test/fixtures/`:
  - search fast and full for a title and for `tests/fixtures/ads/en1_backend.txt`;
  - salary for 2512 (with and without `age_band=25-34`), for an exempt code and for a banned code;
  - a code with a suppressed percentile, found by scanning `data/processed`;
  - compare 2512,2511 with and without an offer;
  - eligibility pass, part-time and invalid (422);
  - timeline, registry and the agent card.
  
  Run it and commit the fixtures
- [ ] T013 Capture the A2A stream bytes. Run `curl -N` with the `SendStreamingMessage` body against the server twice: once with a key and once with no key (the rejected case). Then add one `CancelTask` exchange. Save the raw bytes to `frontend/src/test/fixtures/a2a/*.sse` and a commented copy to `references/a2a-sse-wire.md` (R7). With `OPENROUTER_KEY` absent, record only the no-key and cancel cases, and record the full run in T046

### Frontend: shared state

- [ ] T014 [P] Write `frontend/src/lib/urlState.test.ts`, which must fail first:
  - parse and serialise round-trip `view`, `codes` and `age`;
  - an unknown view falls back to search, duplicates are dropped, and codes past the limit are dropped with a note;
  - an unknown age is ignored;
  - no other key is ever written.
- [ ] T015 Implement `frontend/src/lib/urlState.ts`. T014 passes
- [ ] T016 [P] Write `frontend/src/lib/selection.test.ts`, which must fail first:
  - add, remove, and a duplicate with a note;
  - a fifth add on the chart is refused with a note;
  - an advisor select of several codes keeps the four most recent and lists those left out;
  - the payload is stored per code, and the simulated toggle works per code.
- [ ] T017 Implement `frontend/src/lib/selection.ts` (a reducer). T016 passes
- [ ] T018 Implement the `App.tsx` shell: a view switch from the URL state, navigation for the three views, a drawer toggle, the `Notice` and `SourceLink` components, and validation of URL codes against `/occupations/{code}`. Write the test `App.test.tsx`: a `?view=legal` render shows the legal view's heading, and an unknown code in the URL shows the dropped-code note

**Checkpoint**: `pytest` is green, and `npm test` and `npm run build` are green.

---

## Phase 3: User Story 1 - Find the codes that fit a job (P1) 🎯 MVP

**Independent test**: type a title and paste an ad in the page, and compare the codes with the REST search for the same text.

- [ ] T019 [P] [US1] Write `frontend/src/lib/searchSession.test.ts` with fake timers and a fake fetch. It must fail first:
  - every change sends fast at once and aborts the one in flight;
  - full is sent after 600 ms of no change;
  - an answer for older text is dropped;
  - full replaces fast, and a later fast answer for the same text does not replace full;
  - `parse_ad` follows the line/word rule (R5);
  - empty text sends nothing;
  - text over 20 000 characters is refused with the limit stated;
  - a failed request keeps the previous list and shows an error.
- [ ] T020 [US1] Implement `frontend/src/lib/searchSession.ts`. T019 passes
- [ ] T021 [P] [US1] Write `ScoreStrip.test.tsx`, `AdPassages.test.tsx` and `ResultList.test.tsx` on the recorded fixtures, which must fail first:
  - one cell per method, with `null` shown as "not run";
  - passages show kept or set aside with the reason in words;
  - each result shows the code, the sv/en titles, the matched passage, its flags with source links, `honest_fit` and a select button.
- [ ] T022 [US1] Implement `frontend/src/components/ScoreStrip.tsx`, `AdPassages.tsx` and `ResultList.tsx`. T021 passes
- [ ] T023 [US1] Write `SearchView.test.tsx` (it shows which speed is on screen, shows the fallback reason on a full answer with `fallback_reason`, and selecting a result adds it to the selection and the URL). Then implement `frontend/src/views/SearchView.tsx` until it passes
- [ ] T024 [US1] Prove it by hand: run `npm run build`, start `uv run lonekrav-serve`, type "backend developer" and paste `tests/fixtures/ads/en1_backend.txt`. Take a desktop screenshot and compare the top 5 with `curl -s -XPOST localhost:8000/api/v1/search ...` for the same text and mode

---

## Phase 4: User Story 2 - See what each code pays and what it requires (P1)

**Independent test**: select an exempt and a non-exempt code, and check every mark against the salary payloads.

- [ ] T025 [US2] Load the `dataviz` skill, then follow `viz-distributions` for the bar-and-band encoding. Write the chart's colour tokens (official, low band, simulated, floor) into `frontend/src/index.css` for light and dark, checked with the skill's validator
- [ ] T026 [P] [US2] Write `frontend/src/lib/chartScale.test.ts`, which must fail first. The scale starts at 0, the upper bound is the largest P90 or threshold rounded up to the next 10 000 tick, and value-to-x is linear and the same for every row (R8)
- [ ] T027 [US2] Implement `frontend/src/lib/chartScale.ts`. T026 passes
- [ ] T028 [P] [US2] Write `frontend/src/components/SalaryChart.test.tsx` on the recorded payloads, which must fail first:
  - each bar end, band, median tick and age dot sits at `scale(payload value)`;
  - a null percentile draws nothing and shows the SCB note;
  - the floor line comes from `thresholds[applicable_rule_id]`, or from the eligibility answer when an offer is given;
  - a banned code gets no line and a note;
  - the ghost bar is absent by default, present when toggled, labelled "simulated", and shows its formula;
  - the caption names the table and year with the SCB and Medlingsinstitutet credit;
  - each mark is focusable and announces its value;
  - no fill colour alone distinguishes simulated from official (a dashed outline and a label).
- [ ] T029 [US2] Implement `frontend/src/components/SalaryChart.tsx` (hand-written SVG) and `ChartTable.tsx`, both from one row-mapping function. T028 passes
- [ ] T030 [US2] Wire the chart into `SearchView`: fetch the salary payload per selected code (with `age_band` when chosen), add the age band picker and the per-code simulated toggles, and show the four-code limit note. Prove it by hand at phone and desktop width with 2512, 3511 (exempt) and 5343 (banned), and compare the marks with `curl .../occupations/{code}/salary`

---

## Phase 5: User Story 6 - Run the whole stack with one command (P1)

**Independent test**: `docker compose up --build` on a clean checkout; the page, REST, MCP, the card and both searches work on port 8000; peak memory recorded.

- [ ] T031 [P] [US6] Write `scripts/fetch_models.py`, which downloads each `core.embeddings.SPECS` model at its pinned revision into `HF_HOME` with `huggingface_hub.snapshot_download`. Write a unit test that it requests exactly the SPECS ids and revisions, with `snapshot_download` monkeypatched
- [ ] T032 [US6] Write `docker/Dockerfile` (multi-stage, as in research R10), `.dockerignore` and `docker-compose.yml` (one service, `8000:8000`, `mem_limit: 4g`, environment `OPENROUTER_KEY`, `LONEKRAV_LLM_MODEL` and `LONEKRAV_PUBLIC_URL` interpolated, no `env_file`). Start Docker Desktop, then run `docker compose up --build` and time the build and the start-up (SC-006)
- [ ] T033 [US6] Check the running container by hand:
  - `GET /`, `/api/v1/health`, the card, an MCP `initialize` with `tools/list`, a fast search and a full search;
  - then `docker compose exec` to confirm that `.env` is absent and that the key is only in the environment when given;
  - then cut networking (`docker network disconnect`) and repeat both searches (Story 6 AC5).
  
  Save the commands and output to `references/container-smoke.md`
- [ ] T034 [US6] Write `scripts/container_memory.py`, which samples `docker stats` while running a fast search, a full search with `parse_ad` on the en1 ad, an eligibility check and a compare, and writes `references/container-memory.md` (R11). If the peak is ≥ 4 GB, stop and report to the maintainer (FR-027)
- [ ] T035 [US6] Write `README.md`: what Lönekrav is; local run (`uv sync`, `lonekrav-etl`, `npm ci && npm run build`, `lonekrav-serve`); `docker compose up --build`; every environment variable from data-model.md; the Cloud Run variant (build and push, `gcloud run deploy` with `--memory 4Gi --port` default and `LONEKRAV_PUBLIC_URL`, plus the amd64 CPU-torch note), marked "documented, not deployed"; licences and credits as in `data-dict.yaml`

---

## Phase 6: User Story 3 - Compare codes side by side (P2)

**Independent test**: compare three codes with an offer, and check each column against `POST /compare`.

- [ ] T036 [P] [US3] Write `frontend/src/views/CompareView.test.tsx` on the recorded compare fixtures, which must fail first:
  - columns keep the selection order;
  - each shows sv/en tasks with source, latest salary, threshold, flags and, with an offer, status, margin and warnings;
  - pass and fail use the same styling apart from the status text and icon;
  - `honest_fit` is shown;
  - with fewer than two codes it explains and links to search.
- [ ] T037 [US3] Implement `frontend/src/views/CompareView.tsx` and `components/EligibilityResult.tsx`. T036 passes. Prove it by hand with 2512, 2511 and 3511 and an offer

---

## Phase 7: User Story 4 - Understand the law and check an offer (P2)

**Independent test**: the guide and timeline equal the REST registry and timeline, and the calculator equals `POST /eligibility` for pass, part-time, extension and banned cases.

- [ ] T038 [P] [US4] Write `frontend/src/components/OfferForm.test.tsx`, which must fail first. The fields follow the `Offer` schema; `current_permit_granted_on` appears only for an extension; a 422 detail is mapped to the named field in plain words; and the draft is shared state, never written to storage or the URL
- [ ] T039 [US4] Implement `frontend/src/components/OfferForm.tsx`, with the offer draft in a context shared by compare, the calculator, the chart's floor line and the drawer. T038 passes
- [ ] T040 [P] [US4] Write `frontend/src/views/LegalView.test.tsx` on the recorded registry, timeline and eligibility fixtures, which must fail first:
  - each rule, median, code list, exemption and statement shows its source link and checked-on date;
  - the timeline is in date order and equal to the fixture;
  - the calculator shows status, rule, threshold, margin, warnings (including part-time) and the disclaimer.
- [ ] T041 [US4] Implement `frontend/src/views/LegalView.tsx`. T040 passes. Prove it by hand: full-time pass, part-time, an extension filed in the transition window, and code 5343

---

## Phase 8: User Story 5 - Ask the advisor (P3)

**Independent test**: with the fake advisor, the chart selection follows the run before the memo arrives; with no key, the drawer explains and the page works.

- [ ] T042 [P] [US5] Write `frontend/src/lib/a2aClient.test.ts`, which replays the captured `.sse` bytes from T013, split at awkward chunk boundaries. It must fail first:
  - events come out as task, status, ui_sync, memo and final state;
  - a rejected stream gives the reason;
  - a JSON-RPC error and a broken stream give `failed` and `lost`;
  - cancel posts `CancelTask` with the task id and aborts;
  - the request carries `A2A-Version: 1.0` and one data part.
- [ ] T043 [US5] Implement `frontend/src/lib/a2aClient.ts`. T042 passes
- [ ] T044 [P] [US5] Write `frontend/src/components/AdvisorDrawer.test.tsx`, which must fail first:
  - the third-party notice (from the card description) is shown before the first send;
  - a second send while running is refused;
  - progress lines appear as events arrive;
  - `ui_sync:get_occupation_salary` and `ui_sync:compare_occupations` update the selection, and payloads and dropped codes are noted;
  - the memo renders Markdown without raw HTML and with its footer;
  - unavailable, failed, lost and canceled each show a message and a retry;
  - the offer is sent only if "include my offer" is ticked.
- [ ] T045 [US5] Implement `frontend/src/components/AdvisorDrawer.tsx`. T044 passes
- [ ] T046 [US5] Write `scripts/serve_fake_advisor.py`, which runs `create_app(chat_model=...)` with a scripted model: search, then salary for 2512, then compare 2512,2511, then a short memo. Write `frontend/e2e/advisor.spec.ts` against it: 2512 and 2511 are selected on the chart before the memo arrives (SC-008). Then, if `OPENROUTER_KEY` is present, run the live drawer by hand with the en1 ad, record the full-run wire bytes for T013, and save the timings and a screenshot to `references/web-client-e2e.md`

---

## Phase 9: Polish and evidence

- [ ] T047 Write `frontend/e2e/views.spec.ts`. For search with two codes on the chart, compare and legal, at phone and desktop width:
  - a screenshot to `references/web-client-screenshots/{view}-{project}.png`;
  - `document.documentElement.scrollWidth <= innerWidth`;
  - axe with no serious or critical violations (SC-005, SC-009).
  
  Run it against `lonekrav-serve` and against the container
- [ ] T048 Find a real public job ad (an English-language ad from Platsbanken through the JobSearch API, or one the maintainer supplies) and translate it to Swedish. Write `frontend/e2e/ad-languages.spec.ts`, which pastes each one and records the top three after the full search. They must be the same set (SC-003). Commit only the ad's source link and the codes, in `references/web-client-e2e.md`, and keep the ad text in the scratchpad
- [ ] T049 Measure SC-001 and SC-002 in Playwright on the reference machine (keystroke to list update; pause to full ranking for the 600-word ad), and record the numbers in `references/web-client-e2e.md`
- [ ] T050 [P] Regenerate `references/api-smoke.md` with `scripts/api_smoke.py`. The only differences allowed are the timestamp and the new `/legal/registry` route, if the smoke script lists routes
- [ ] T051 Write `docs/walkthroughs/004-web-client-docker.md` with the walkthrough skill (snippets emitted with `sed`). Update CLAUDE.md ("Things worked out in Feature 004"; the `/` serving note; the frontend commands) and `references/development-plan.md` ("As built")
- [ ] T052 Run `/speckit-converge`, then run the full gates: `rtk proxy uv run pytest -q`, `uv run pytest -m benchmark -q` (with the server stopped), `npm test`, `npm run build`, and `ruff`
- [ ] T053 Open the PR with the evidence (screenshots, memory, e2e, smoke). Request a Copilot review with the `gh api` command in memory, then fix or answer every comment

---

## Dependencies

- Setup (T001–T003) comes before Foundational (T004–T018), which comes before every story.
- US1 (T019–T024) comes before US2's wiring (T030); the chart itself (T025–T029) can be built in parallel with US1.
- US6 (T031–T035) needs a building page (T001) and the backend serving (T005). It is best done after US2, so the image carries a useful page.
- US3 and US4 need the selection (T017) and, for the offer, T039. US3's offer column waits for T039.
- US5 needs T013 (the wire bytes) and the selection.
- Polish comes last.

## Parallel opportunities

- T004, T006, T008 and T010 are separate test files.
- T014 and T016 are separate libs.
- T019, T021, T026 and T028 can all be written ahead of their implementations.
- The US3 and US4 tests (T036, T038 and T040) can be written in parallel.

## Implementation strategy

The MVP is Phases 1–4: search plus the chart, served by `lonekrav-serve`. Then the container (US6)
makes it portable. Compare and legal follow, and the advisor drawer last. Each phase ends with a
by-hand proof in a browser.
