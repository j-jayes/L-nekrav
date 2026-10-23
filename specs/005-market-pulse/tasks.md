# Tasks: Market pulse

**Input**: Design documents from `specs/005-market-pulse/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: required (Constitution IV, red/green). Each test task must be seen to fail before the
task after it is implemented.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [x] T001 Amend `.specify/memory/constitution.md` (PATCH): add the JobSearch and historical ads APIs (CC0) and SCB TAB5696 to Technology and Data Constraints, with a sync-impact note (research R8)
- [x] T002 [P] Add `jobtech_jobsearch` and `jobtech_historical` to `Source` in `src/lonekrav/core/models.py`
- [x] T003 [P] Extend `scripts/cut_fixtures.py` to cut real slices into `tests/fixtures/`: TAB5696 for codes 2512, 1211, 1212, 4430, 2221 (json-stat2, `lang=en`); a JobSearch `search` answer for 2512's concept and for a concept with an ad with no county, if one is found; historical answers for 2512 for 2016 and 2025. Run it and commit the slices

## Phase 2: Foundational

- [x] T004 Write a failing test in `tests/unit/test_market_models.py` for `RegionalSalary` (independently nullable `mean` and `employees`, `reference_year == year`, computed `suppressed`) and `YearlyAds` (`ads >= 0`, `year >= 2016`)
- [x] T005 Implement `RegionalSalary` and `YearlyAds` in `src/lonekrav/core/models.py`

## Phase 3: User Story 1 — Live demand (P1) 🎯 MVP

**Goal**: one code's open ads, positions and counties, live, with shared and missing concepts labelled and failure reported without a number.
**Independent test**: `GET /api/v1/occupations/2512/market` gives `live` equal to JobSearch's own count; 1211 names 1212; 4430 gives `no_concept`; an unreachable URL gives `unavailable` within 5 s.

- [x] T006 [US1] Write failing tests in `tests/unit/test_market.py` for `parse_live` on the T003 fixture: ads, positions, counties ordered by count, `no_county = total − Σ`, and `unexpected response` for a body without `total`
- [x] T007 [US1] Write failing tests in `tests/unit/test_market.py` for `LiveCache` with a fake fetcher and clock: a reuse within 15 min keeps `fetched_at` and makes one fetch; a refetch after 15 min; an unavailable answer is not cached; a timeout, connection error, HTTP 503 and bad JSON each map to their `reason`
- [x] T008 [US1] Implement `CountyCount`, `LiveDemand`, `parse_live`, `http_fetcher` (httpx, two requests per count, 2 s timeout each, User-Agent, base URL from `LONEKRAV_JOBSEARCH_URL`, defaulting to the real API) and `LiveCache` in `src/lonekrav/core/market.py`
- [x] T009 [US1] Write failing tests in `tests/unit/test_market.py` for `market()`: `shared_with` from profiles with the same concept (1211 ↔ 1212), `no_concept` for a profile without a concept id (no fetch made), and `notice` equal to `MARKET_NOTICE`, which contains `HONEST_FIT`'s rule that the code must match the duties
- [x] T010 [US1] Implement `MarketAnswer`, `MARKET_NOTICE` and `market()` in `src/lonekrav/core/market.py`, and `Service.market(code)` in `src/lonekrav/core/service.py` (with a `live: LiveCache` field, defaulting to the real fetcher); `UnknownCode` for an unknown code
- [x] T011 [US1] Write failing tests in `tests/integration/test_market_api.py`: `GET /api/v1/occupations/{code}/market` gives 200 with a fake fetcher, 404 for 9999, and 200 with `live.status="unavailable"` when the fetcher raises
- [x] T012 [US1] Add the route in `src/lonekrav/api/v1.py`, and let `create_app` in `src/lonekrav/app.py` accept an injected `LiveCache` for tests
- [x] T013 [US1] Add `tests/integration/test_market_live.py` (marker `live`, skipped when the network is unavailable; widen the `live` marker's description in `pyproject.toml` to "calls a real external service"): for 2512, the answer's `ads` is within 2 % of a direct JobSearch call made in the same test, since ads can change in between. The exact same-minute check for 10 codes (SC-001) is T038

## Phase 4: User Story 2 — Regional pay (P2)

**Goal**: SCB TAB5696 means per national area for the latest year, built ahead of time, with suppression kept.
**Independent test**: the parsed fixture slice matches SCB's cells, nulls stay null, and the market answer's `regional` lists `SE` first.

- [x] T014 [US2] Write failing tests in `tests/unit/test_scb_regional.py` for `scb_pxweb.parse_regional` on the T003 slice: 2512 in 2025 for `SE` is 55 500 ± 940 with 113 100 employees; `SE21` has a mean and null employees; codes 0001 and 0002 are dropped and 0000 is kept, as for TAB5932; and every row's table, reference year and fetched_at are set
- [x] T015 [US2] Implement the TAB5696 fetch (in `scb_pxweb.fetch`, `lang=en`, the three content codes) and `parse_regional`/`build_regional` in `src/lonekrav/etl/scb_pxweb.py`; add `write_regional`/`load_regional` (`data/processed/salary_regional.parquet`) in `src/lonekrav/core/salary.py`; call it from `pipeline.build`
- [x] T016 [US2] Write failing tests in `tests/unit/test_market.py` for the regional part of `market()`: only the latest year, `SE` first and then by area code, an empty list and null `regional_year` for a code with no rows
- [x] T017 [US2] Implement the regional part in `src/lonekrav/core/market.py`, and load `salary_regional.parquet` into `Service` in `src/lonekrav/app.py`. Update the test fixtures in `tests/conftest.py`
- [x] T018 [US2] Run `lonekrav-etl fetch --only scb_pxweb` and `lonekrav-etl build` for real. Commit `salary_regional.parquet`. Add `tests/integration/test_regional_data.py`: the committed `SE` mean equals TAB5932's mean for each code and year present in both (research R3 cross-check)
- [x] T019 [US2] Record `salary_regional` in `data/processed/data-dict.yaml` (provenance, CC0, Medlingsinstitutet / SCB credit, the suppression note) and run `data-dict validate-data`

## Phase 5: User Story 3 — Yearly demand (P3)

**Goal**: ads published per full year since 2016 for each concept, built ahead of time; a missed year fails the build.
**Independent test**: building from the fixtures gives 2016 = 16 406 and 2025 = 30 304 for 2512's concept, and a missing file raises.

- [x] T020 [US3] Write failing tests in `tests/unit/test_jobsearch_history.py`: `years(today)` gives 2016 to the last full year (a build on 2027-01-02 includes 2026); `parse_year` reads `total.value`; `build_history` raises naming the concept and year when one is missing, and stores 0 as 0
- [x] T021 [US3] Implement `src/lonekrav/etl/jobsearch.py`: `fetch_history(raw, concepts, force)` with one `cached_get` file per concept-year under `data/raw/jobsearch_history/` on 4 threads, then `years` and `build_history`; add `write_history`/`load_history` (`data/processed/ad_history.parquet`); wire `jobsearch_history` into `pipeline.fetch`/`build` and `cli.SOURCES`
- [x] T022 [US3] Write failing tests for the history part of `market()` in `tests/unit/test_market.py`: rows ascending by year for the code's concept, and `history_status="no_concept"` with no rows for 4430
- [x] T023 [US3] Implement the history part in `src/lonekrav/core/market.py`, and load `ad_history.parquet` into `Service` in `src/lonekrav/app.py`
- [x] T024 [US3] Run the real history fetch and build, timing them. Check on 2512 that the months of 2025 add up to its yearly count (research R4), and record the result. Commit `ad_history.parquet`. Add a test that every concept in the committed profiles has one row per year (SC-005)
- [x] T025 [US3] Record `ad_history` in `data/processed/data-dict.yaml` (provenance, CC0, ads not positions, from 2016) and run `data-dict validate-data`

## Phase 6: User Story 4 — MCP and advisor (P3)

**Goal**: the same market answer through MCP; the advisor may cite it and never chooses by it.
**Independent test**: the MCP tool equals REST for a code; the advisor's prompt and a scripted run pass the honest-fit checks.

- [x] T026 [US4] Write a failing test in `tests/integration/test_mcp.py`: `get_occupation_market` is listed, returns the same JSON as REST for 2512 with the same fake fetcher, and returns REST's text as a ToolError for 9999
- [x] T027 [US4] Add the tool to `src/lonekrav/protocols/mcp_server.py` with the description from contracts/mcp.md
- [ ] T028 [US4] Write a failing test in `tests/unit/test_agent_loop.py` (or the existing prompt test) that `SYSTEM_PROMPT` names `get_occupation_market` and forbids preferring a code by demand or pay; extend the existing honest-fit wording test to cover the tool's description and `MARKET_NOTICE`
- [ ] T029 [US4] Update `SYSTEM_PROMPT` in `src/lonekrav/protocols/agent/loop.py` (contracts/mcp.md)

## Phase 7: The page (US1–US3 in the compare view)

**Goal**: the market panel under each compare column.
**Independent test**: Vitest on recorded answers covers each status; Playwright screenshots at 390 and 1280 px pass axe.

- [x] T030 Regenerate the schema and types (`uv run python scripts/export_openapi.py && (cd frontend && npm run gen)`); `test_openapi_drift.py` passes
- [ ] T031 [P] Extend `scripts/record_api_fixtures.py` to record `market-2512.json`, `market-1211.json`, `market-4430.json` and `market-unavailable.json` (the latter with `LONEKRAV_JOBSEARCH_URL` pointed at a closed port) into `frontend/src/test/fixtures/`, and run it against a local server
- [ ] T032 Write failing tests in `frontend/src/components/MarketPanel.test.tsx`: available (counts, top 5 counties, details for the rest, source and fetched time), shared (names 1212), no_concept (no number), unavailable (reason, no number), regional (floor sentence, mean ± margin, "not published" for null), history (bar per year, table view, a zero year labelled 0), the panel's own request failing, and the notice shown
- [ ] T033 Implement `frontend/src/components/MarketPanel.tsx` (contracts/ui.md, research R7); load the `dataviz` skill and draw the chart at the measured width
- [ ] T034 Write a failing test in `frontend/src/views/CompareView.test.tsx` that each column shows a market panel for its code, including codes added by the advisor
- [ ] T035 Render `MarketPanel` in each column of `frontend/src/views/CompareView.tsx`, passing the column's floor
- [ ] T036 Extend `frontend/e2e/views.spec.ts` to wait for the market panel in the compare view; refresh `references/web-client-screenshots/compare-{phone,desktop}.png`; there must be no sideways scroll and no serious or critical axe violations

## Phase 8: Polish and evidence

- [ ] T037 Run the gates: `rtk proxy uv run pytest -q`, `-m benchmark` (with the server stopped), `-m live`, `npm test`, `npx playwright test`, and `ruff check`
- [ ] T038 Write `references/market-pulse.md`: real curl answers for 2512, 1211 and 4430 and the unavailable case, with times (SC-002, SC-003), a live comparison against JobSearch for 10 sampled codes (SC-001), the history fetch's duration, and the month-sum check
- [ ] T039 Regenerate `references/api-smoke.md` with `scripts/api_smoke.py` (adding the market route)
- [ ] T040 Rebuild the container and run `scripts/container_smoke.py` with `LONEKRAV_PORT=8001`; confirm the market route from inside the image, and record it in `references/container-smoke.md`
- [ ] T041 Update `README.md` (data and credits, the market route, `LONEKRAV_JOBSEARCH_URL` in the settings table), `references/development-plan.md` (the 005 as-built note, correcting TAB4185 to TAB5696), `CLAUDE.md` ("Things worked out in Feature 005") and `docs/walkthroughs/005-market-pulse.md` (walkthrough skill)
- [ ] T042 Open the PR with the evidence, request the Copilot review, and answer every comment

## Dependencies

- Setup (T001–T003) → Foundational (T004–T005) → US1 (T006–T013) is the MVP.
- US2 (T014–T019) and US3 (T020–T025) depend only on Foundational and on `market()` from T010,
  and can run in either order.
- US4 (T026–T029) needs T010.
- The page (T030–T036) needs US1–US3 for its fixtures.
- Polish comes last.

## Parallel opportunities

- T002 and T003.
- The US2 parser tests (T014) and the US3 history tests (T020) touch different files once T010 is
  done.
- T031 fixture recording alongside T032.

## Implementation strategy

MVP = US1 through REST (T001–T012). Then regional pay, history, MCP/advisor, the page, and the
evidence, committing after each phase.
