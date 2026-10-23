# Research: Market pulse

Every fact here was probed live on 2026-10-23, unless it says otherwise. The probe files are in
the session scratchpad and were not committed. The fixtures are cut from the same endpoints by
`scripts/cut_fixtures.py`.

## R1. The live ad interface (JobSearch)

- **Decision**: `GET https://jobsearch.api.jobtechdev.se/search?occupation-group={concept}&limit=0&stats=region&stats.limit=30`
  with Lönekrav's User-Agent and a 3 s timeout. The fields used are:
  - `total.value`: the number of ads;
  - `positions`: the number of positions;
  - `stats[0].values[]`: the counties, each with `term`, `code`, `concept_id` and `count`.

  Ads with no county are `total − Σcounts`, shown as "no county given" when greater than zero.
- **Evidence**:
  - The request needs no key and answered 200 in 0.36 s.
  - For `DJh5_yyF_hEM` (2512) it returned 1 183 ads, 1 569 positions and 488 in Stockholms län.
  - `stats.limit` above 30 returns 400 ("not less or equal to 30"); Sweden has 21 counties.
  - `swagger.json` gives version 1.37.0, with the licence "Ads are licensed under CC0".
- **Alternatives**: one request with `stats=occupation-group` for every code is not possible
  (capped at 30 values). A nightly snapshot was rejected: the spec asks for live counts.

## R2. Live cache and failure

- **Decision**: `LiveCache` lives in `core/market.py`. It is a dict from concept to `LiveDemand`,
  guarded by a `threading.Lock`, with a TTL of 15 minutes and an injected clock and fetcher.
  - Only answers with status `available` are cached; an "unavailable" answer is retried on the
    next request.
  - A timeout, a connection error, a non-2xx status or an unparseable body gives
    `status="unavailable"` with a reason (`timeout`, `http 503`, `connection error`,
    `unexpected response`), and no number.
- **Rationale**: REST routes and MCP tools are synchronous here (they run in the thread pool), so
  a lock is enough. With a 3 s timeout, SC-003 (5 s) holds even for the slowest failure.
- **Base URL setting**: `LONEKRAV_JOBSEARCH_URL` (default the real API) exists only so that the
  failure path can be proven against a running server (SC-003) and in e2e. Unit tests inject the
  fetcher instead.
- **Alternatives**: an LRU library (not needed for about 400 keys); caching failures (that would
  hide a recovered API for 15 minutes).

## R3. Regional pay: SCB TAB5696

- **Decision**: fetch `TAB5696` (PxWeb v2, `lang=en`, json-stat2) with `Region=*`, `Sektor=0`,
  `Kon=1+2`, `Yrke2012=*`, `Tid=*`, and
  `ContentsCode=000007AS,000007AU,000007AP` (monthly salary, its 95 % CI, number of employees).
  - Store every year (2023–2025) in `salary_regional.parquet`; serve the latest year per code.
  - The English labels supply the area names (`SE`: Sweden, `SE11`: Stockholm, `SE12`:
    East-Central Sweden, …).
- **Evidence**:
  - One request returns all 34 992 cells (391 kB, 1.4 s); 14 495 are null (status `..`).
  - For 2512 in 2025, Sweden shows a mean of 55 500 ± 940 with 113 100 employees. Four areas
    have a published mean but a suppressed employee count. So each field is nullable on its
    own, which the model must allow.
  - The CI is one ± figure, as in TAB5932 (`mean_ci95`), so it is stored in the same way.
  - The metadata was updated 2026-06-16; the table is SCB open data (CC0), and the credit is the
    same as for the other salary tables (Medlingsinstitutet / SCB).
- **Not TAB4185**: its label is "Genomsnittlig månadslön, lönespridning m.m. inom regioner",
  salaries *within the regions* (the county health-care employers), not by area. The
  development plan's mention of it is corrected in the plan's as-built note.
- **Cross-check**: the national row (`SE`) should equal TAB5932's mean for the same code and
  year. A test asserts this over the committed data, which catches a wrong table or content code.
- **Alternatives**: TAB4262 (2014–2022) is out of scope, since the latest year is enough. County
  pay per 4-digit code is not published.

## R4. Yearly demand: the historical ads API

- **Decision**: `GET https://historical.api.jobtechdev.se/search?occupation-group={concept}&limit=0&historical-from={y}-01-01T00:00:00&historical-to={y}-12-31T23:59:59`
  for each concept and each year from 2016 to the last full year (2025 in a 2026 build).
  - Store `total.value` as the year's ad count.
  - Each answer is cached as its own raw file through `cached_get`, so an interrupted fetch
    resumes. A failed request raises `FetchError`, which fails the build (FR-014).
  - The fetch runs on 4 threads.
- **Evidence**:
  - Version 1.32.2, with the licence "Ads are licensed under CC0".
  - For 2512: 2016 = 16 406, 2020 = 17 910, 2024 = 21 634, 2025 = 30 304, 2026 (to date) =
    17 351.
  - 2006–2015 return 0 for this concept, as coded ads start in 2016.
  - With `stats=region`, `positions` came back 0 for a year with ads, so history counts ads only.
  - A request takes about 0.37 s, so 3 970 requests take about 25 minutes serially and about 6
    minutes on 4 threads.
- **To confirm in implementation**: that `historical-from`/`historical-to` filter by publication
  date. Check that the months of one year add up to the year's count, and record the result in
  `references/market-pulse.md`.
- **Alternatives**: `published-after`/`published-before` (equivalent if the check above holds);
  counting history per county (not asked for, and 22 times the requests).

## R5. Shared and missing concepts

- **Decision**: the profile already has `jobtech_concept_id` and `jobtech_shared`. The codes that
  share a count are the profiles with the same concept id, worked out in core from the loaded
  profiles.
  - With no concept id (4430, 5322, 5324, 7619), the status is `no_concept` and there is no
    number.
  - A shared concept gives the status `available` plus a non-empty `shared_with` list.
- **Rationale**: no new data is needed, and REST, MCP and the page get the same labels.

## R6. Surfaces

- **REST**: `GET /api/v1/occupations/{code}/market` returns `MarketAnswer`; an unknown code gives
  404, as for `/salary`.
- **MCP**: the tool `get_occupation_market(code)`. The advisor lists the MCP tools at run time,
  so it gets the tool with no change to the loop.
- **Advisor**: `SYSTEM_PROMPT` gains one step. The advisor may call `get_occupation_market` for
  the plausible codes and cite the counts and means with their source and time. Demand and pay
  must never be a reason to choose or rank a code.
  - The executor's `ui_sync` artefacts stay limited to salary and compare, so the drawer is
    unchanged.
- **Page**: `CompareView` renders `MarketPanel` per column, fetching
  `/occupations/{code}/market`. Types come from the regenerated schema (the drift test).

## R7. The panel's chart

- **Decision**: yearly ads are one series, so the chart is a bar chart in hand-written SVG,
  drawn at the measured width as in `SalaryChart`.
  - It uses one accent colour and no legend; the title names the series.
  - Each bar gets a `<title>` tooltip, and a table view sits in a `<details>`.
  - Zero is drawn as an empty bar with a 0 label, so a zero year is visibly not missing.
- **Regional pay**: a table (area, mean ± margin, employees), not a chart, because FR-010 forbids
  drawing it beside the floor. The floor appears as a sentence above the table: "The floor is
  X SEK in every area; it comes from the national median. These are means."
- **Rationale**: the dataviz skill says a single series needs no legend, that a table view is
  required, and to choose the plain table when a chart would invite a wrong comparison.

## R8. Constitution amendment (PATCH)

The Technology and Data Constraints section lists the data sources. Add "Arbetsförmedlingen's
JobSearch and historical ads APIs (CC0)" and "SCB TAB5696 (regional means)", and bump the patch
version with a sync-impact note. No principle changes.
