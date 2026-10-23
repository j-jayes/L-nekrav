# Implementation Plan: Market pulse

**Branch**: `005-market-pulse` | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/005-market-pulse/spec.md`

## Summary

Feature 005 adds market context for each SSYK code, from three sources:
- **Live demand**: the open-ad count, positions and ads per county, from Arbetsförmedlingen's
  JobSearch API. It is fetched when a code is requested and reused for 15 minutes (R1, R2).
- **Regional pay**: SCB TAB5696's mean monthly salary, its 95 % margin and the number of
  employees, for Sweden and its 8 national areas. It is built by the ETL into a committed
  Parquet file (R3).
- **Yearly demand**: the number of ads published per full year from 2016, from the historical
  ads API. It is also built by the ETL and committed (R4).

One core function, `Service.market(code)`, answers for all surfaces:
- REST `GET /api/v1/occupations/{code}/market`;
- the MCP tool `get_occupation_market`, which the advisor reaches through the MCP tools it
  already lists;
- a market panel under each column in the page's compare view (R6, R7).

## Technical Context

**Language/Version**: Python 3.12 (uv); TypeScript 5.9 on Node 22 for the page.

**Primary Dependencies**: no new ones. httpx, which the ETL already uses, makes the live call;
the page uses its existing stack.

**Storage**: two new committed artefacts in `data/processed/`: `salary_regional.parquet` and
`ad_history.parquet`. The live counts live in an in-memory cache with a 15-minute life. Raw
downloads stay under `data/raw/` (`pxweb/TAB5696.json`, and one file per concept per year under
`jobsearch_history/`).

**Testing**:
- pytest, offline by default: parsers on fixture slices cut from real responses
  (`scripts/cut_fixtures.py`), the live client with an injected fetcher and clock, the service,
  REST, MCP and drift.
- One `live`-marked test calls the real JobSearch API, and is skipped without a network.
- Vitest on recorded real responses for the panel; Playwright screenshots and axe for the compare
  view.

**Target Platform**: unchanged (local `lonekrav-serve`, and the container). The container needs
outbound HTTPS for the live count only; without it, the count says it is unavailable.

**Project Type**: a web service plus its single-page client.

**Performance Goals**:
- A market answer with a live fetch arrives within 2 s; a reused one within 0.1 s (SC-002).
- With JobSearch down, an answer arrives within 5 s (SC-003). The live call times out at 3 s.

**Constraints**:
- No count or salary is estimated or carried over (FR-005, Principle II).
- Regional means are never drawn as a threshold (FR-010).
- The default test run stays offline (FR-007).
- The history build fails loudly on a missed year (FR-014).

**Scale/Scope**:
- Live demand: about 397 JobTech concepts, at most 4 live calls per compare view.
- Regional pay: 34 992 cells (9 areas × 432 codes × 3 contents × 3 years), in one SCB request.
- Yearly demand: about 3 970 history requests (397 concepts × 10 years), cached per file.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|---|---|---|
| I. Core first, adapters thin | `core/market.py` holds the parsers, the cache and the answer, with the HTTP fetch injected. REST and MCP make one call into `Service.market`, which is plain pydantic, with no FastAPI in core. | Pass |
| II. Data integrity | Each regional row carries `source_table`, `reference_year` and `fetched_at`, and suppressed cells stay `null`. Counts carry their source and time. An "unavailable" answer carries no number. Both new datasets go in `data-dict.yaml`. | Pass |
| II. Legal constants | Nothing new; the floor comes from the existing payload. | Pass |
| III. Honest fit | The panel, the tool description and the advisor prompt all state that demand and pay are context, never a reason to choose a code. The existing honest-fit tests are extended. | Pass |
| IV. Test-first, proven by hand | Red/green per task. Evidence: curl of the market route, a live probe, and screenshots. | Pass |
| V. Compact and portable | No new service; the image gains two small files. Live data degrades without network. | Pass |
| VI. Simplicity | One cache dict with a lock, no new framework, no history API at run time. | Pass |
| Technology and data constraints | The list of data sources does not name the JobSearch and historical ads APIs or TAB5696. **A PATCH amendment adds them (T001)**; it clarifies the list and changes no principle. | Amend |

Re-check after design: unchanged. The data model adds models only in `core/models.py` and
`core/market.py`, shared by every surface.

## Project Structure

### Documentation (this feature)

```text
specs/005-market-pulse/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── http.md        # GET /api/v1/occupations/{code}/market
│   ├── mcp.md         # get_occupation_market tool
│   └── ui.md          # the compare view's market panel
└── tasks.md
```

### Source Code (repository root)

```text
src/lonekrav/
├── core/
│   ├── market.py          # NEW: LiveDemand, parse_live, LiveCache, MarketAnswer, market()
│   ├── models.py          # + RegionalSalary, YearlyAds
│   ├── service.py         # + Service.market, + regional and history data
│   └── salary.py          # + write/load for salary_regional.parquet
├── etl/
│   ├── scb_pxweb.py       # + TAB5696 fetch and parse_regional
│   ├── jobsearch.py       # NEW: history fetch (one cached file per concept-year) and build
│   ├── pipeline.py        # fetch/build steps for both
│   └── cli.py             # + "scb_regional", "jobsearch_history" sources
├── api/v1.py              # + GET /occupations/{code}/market
├── protocols/mcp_server.py        # + get_occupation_market
├── protocols/agent/loop.py        # SYSTEM_PROMPT: may cite the market, never choose by it
└── app.py                 # loads the two new artefacts into Service
data/processed/{salary_regional,ad_history}.parquet, data-dict.yaml
frontend/src/
├── components/MarketPanel.tsx (+ .test.tsx)   # live counts, regional table, yearly chart
├── views/CompareView.tsx                       # one panel per column
└── test/fixtures/market-*.json                 # recorded real answers
tests/unit/test_market.py, test_scb_regional.py, test_jobsearch_history.py
tests/integration/test_market_api.py, test_mcp.py (+tool), test_market_live.py (live marker)
scripts/cut_fixtures.py (+ slices), scripts/record_api_fixtures.py (+ market)
```

**Structure Decision**: the existing monorepo layout. One new core module and one new ETL module;
everything else extends existing files.

## Complexity Tracking

No violations to justify. The live cache is the one stateful piece in core. It is a dict guarded
by a lock with an injected clock, and Service owns it, because FR-006 needs it.
