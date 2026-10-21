---
description: "Task list for Feature 002: occupation search, permit eligibility and salary API"
---

# Tasks: Occupation Search, Permit Eligibility and Salary API

**Input**: `specs/002-search-eligibility-api/` (spec.md, plan.md, research.md, data-model.md,
contracts/api-v1.md, quickstart.md, checklists/legal-and-gate.md)

**Tests**: Required. Constitution Principle IV mandates red/green TDD. Every test task MUST be run
and seen to fail for the stated reason before its implementation task starts.

**Fixtures**: the default `uv run pytest` stays offline. Search and API tests use a fixture index
built with the FakeEmbedder, as `tests/integration/test_index_search.py` does (fixture codes 0110,
1211, 1212, 2421, 2512, 3511, 4430, 5322, 5343, 9210). Real models run only under `-m benchmark`.

**Legal literals**: amounts, percentages and dates may appear only in `legal_constants.yaml` and in
tests of the registry or eligibility (Principle II, SC-002). Other tests read them from the registry.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1–US7 from spec.md

---

## Phase 1: Setup

- [X] T001 Add `fastapi` and `uvicorn` with `uv add`; register `lonekrav-serve = "lonekrav.app:main"` in `pyproject.toml`; create `src/lonekrav/api/__init__.py`
- [X] T002 [P] Copy `data/processed/benchmark_results.json` to `data/processed/benchmark_results_001.json` (the 001 baseline FR-019 keeps for comparison) and commit it

---

## Phase 2: Foundational (blocks every story)

### Legal registry (FR-001–FR-005a)

- [X] T003 [P] Test `tests/unit/test_legal.py`: the registry loads and validates; every row has `source.url` and `checked_on`; medians are contiguous (each `effective_to` is the day before the next `effective_from`); for every median, the 90 %, 75 % and 80 % amounts rounded half up equal Migrationsverket's table in research R6 (the one place these literals are written); `median_on(2026-06-15)` is 37 100 and `median_on(2026-06-16)` is 38 300; `codes_on("exempt_75", 2026-10-21)` has the 27 SFS codes; `timeline()` is date-ordered and includes the 13 000 flat rule, the 80 % rule from 2023-11-01, the 90 % rule from 2026-06-01 and the transition end 2026-12-01; a loader given a row without a source raises an error naming the row
- [X] T004 Write `src/lonekrav/core/legal_constants.yaml` from research R6 (medians 2021–2026 with dates and SCB reference years; rules `flat_13000`, `maintenance_80`, `salary_90`, `salary_75_exempt`, `transition_maintenance_80` with `permits_granted_before`; `median_publication_window` (16 and 22 June); statements `part_time` (Migrationsverket employees page) and `partial_ban_9210`; code lists `exempt_75`, `banned`, `partially_banned` from `core/legal_flags.py`; the four personal exemptions with conditions and their first-permit-only flag; every row with source URL and `checked_on: 2026-10-21`) and implement `src/lonekrav/core/legal.py` (models from data-model.md, `load_registry()` cached, `median_on`, `rule`, `codes_on`, `timeline`, Decimal half-up rounding) until T003 passes
- [X] T005 [P] Test in `tests/unit/test_legal.py`: given today's date, the registry holds a median that took effect this year whenever today is on or after 23 June (FR-005a); written with an injectable `today` so the rule itself is tested both ways
- [X] T006 Make T005 pass in `src/lonekrav/core/legal.py` (`registry_is_current(today)`, reading the window from the registry; no date literal in code)
- [X] T007 Change `src/lonekrav/core/legal_flags.py` to read its code sets and citation from the registry, keeping `flags_for()`'s signature, and add an optional `checked_on` to `LegalFlag` in `src/lonekrav/core/models.py`, filled from the registry (committed profiles stay valid). `tests/unit/test_legal_flags.py` stays green, plus one new assertion that flags carry `checked_on`. Search hits and comparison columns take flags from `flags_for()`, not from the profile JSON

### App skeleton (FR-029–FR-032)

- [X] T008 [P] Test `tests/integration/test_api.py`: `create_app(engine=...)` with a fixture engine serves `GET /api/v1/health` with status ok; `GET /api/v1/openapi.json` is valid OpenAPI; a route that raises an unexpected error returns 500 with body `{"detail": "internal error"}` and no path or traceback; no request body appears in captured logs (caplog) for a POST; the app starts and serves with `OPENROUTER_KEY` unset (FR-032)
- [X] T009 Implement `src/lonekrav/app.py` (`create_app()`, lifespan that builds the search engine unless one is injected, catch-all 500 handler, access logging of method/path/status/duration only, `main()` running uvicorn on 127.0.0.1:8000) and `src/lonekrav/api/v1.py` (router with `/health`) until T008 passes
- [X] T010 Add an `api_client` fixture in `tests/conftest.py` that builds the fixture index (reuse `build_index` from `tests/integration/test_index_search.py`, moved into `tests/conftest.py`) and returns a `TestClient`

**Checkpoint**: registry and app run; `uv run pytest` green.

---

## Phase 3: User Story 3 — Swedish search is as good as English (P1, gates the merge)

**Goal**: explain the gap, fix the benchmark leak, fix the fusion, and pass the gates in FR-020.
Done first because the diagnosis could change the search design (plan, implementation order 1).

**Independent test**: `uv run lonekrav-etl benchmark` prints the diagnosis and both modes;
`uv run pytest -m benchmark` passes (final run in T060 after US2).

- [ ] T011 [P] [US3] Test `tests/unit/test_leak_check.py` for the FR-018a rule: "business manager" leaks into "Business managers are responsible…" (+1); "sjuksköterska" leaks into "sjuksköterskan" (+1); "manage" does not leak into "management" (+4); a phrase that starts mid-word ("chef" in "kökschef") does not count; matching is case-insensitive in both languages
- [ ] T012 [US3] Make `_Leaks` in `src/lonekrav/etl/benchmark.py` use the FR-018a rule for both languages until T011 passes
- [ ] T013 [P] [US3] Test `tests/unit/test_generated_set.py` (extend): a generated pair whose English label leaks takes the next exact/close ESCO label that does not leak; if none, the query keeps its Swedish text and `text_en` is None
- [ ] T014 [US3] Implement T013 in `generate_queries` in `src/lonekrav/etl/benchmark.py`
- [ ] T015 [P] [US3] Test `tests/unit/test_metrics.py` (extend): `diagnose(per_query_ranks)` returns recall@5 by language × origin × form (`single` or `slash`) with n, and the share of the fused gap each group explains; `evaluate` keeps per-query ranks so diagnose can run
- [ ] T016 [US3] Implement `diagnose` and per-query ranks in `src/lonekrav/etl/benchmark.py`; `run()` writes `diagnosis`, `n` beside every metric, and `previous` (headline numbers read from `benchmark_results_001.json`); `table()` prints old beside new (T015)
- [ ] T017 [US3] Run for real: `lonekrav-etl build && lonekrav-etl index && lonekrav-etl benchmark`. Record paired n, the diagnosis table and old vs new in `references/benchmark-diagnosis-002.md`. If paired n < 60, stop and ask the maintainer (FR-020a)
- [ ] T018 [P] [US3] Test `tests/unit/test_fusion.py` (extend): `fuse(per_method, weights={"bm25": 0.5})` scales each method's RRF term by its weight; default weights reproduce today's ranking exactly
- [ ] T019 [US3] Add `weights` to `fuse` in `src/lonekrav/core/search.py` with a module constant `WEIGHTS` (default all 1.0) until T018 passes
- [ ] T020 [US3] Choose the BM25 weight on the generated queries only (sweep 0.0–1.0 in steps of 0.1 in a scratch script that calls `evaluate`), confirm on the hand-written queries, set `WEIGHTS` in `src/lonekrav/core/search.py`, and record the sweep and choice in `references/benchmark-diagnosis-002.md` (FR-020a). If the gates still fail, try analyser changes in `src/lonekrav/core/text.py` with a failing test in `tests/unit/test_text.py` first; if they still fail, stop and ask the maintainer
- [ ] T021 [US3] Rewrite `tests/eval/test_benchmark.py` to FR-020: full-mode gates on all paired queries per language (recall ≥ 0.80, gap ≤ 0.05, fused ≥ each method), hand-written overlap ≥ 0.80 in full mode, fast-mode recall ≥ 0.80 per language, and a guard that paired n ≥ 60; `run()` evaluates both modes (fast = kblab + bm25)

**Checkpoint**: diagnosis recorded; leak fixed; fusion weights chosen. Gate passes are confirmed in T060 once US2's search changes are in.

---

## Phase 4: User Story 1 — check an offer against the salary requirement (P1) 🎯 MVP

**Goal**: `POST /api/v1/eligibility` answers every scenario in Story 1 correctly with sources.

**Independent test**: quickstart §3 eligibility rows by curl; `tests/unit/test_eligibility.py` green.

### Tests (write first, see them fail)

- [ ] T022 [P] [US1] `tests/unit/test_eligibility.py`, request validation: `fte_percent` 0 or 101, salary ≤ 0, unknown or malformed code, extension without `current_permit_granted_on`, first permit with one, `decided_on` before `filed_on`, `former_student_researcher` on an extension, duplicate exemptions: each raises a validation error naming the field
- [ ] T023 [P] [US1] `tests/unit/test_eligibility.py`, rule selection, one test per Story 1 scenario 1–12 and per edge case: 2512 filed 2026-06-16 → `salary_90`, 34 470, margin 5 530; filed 2026-06-15 → 33 390; 3511 → 28 725; 5343 → `not_permitted` with no threshold or margin and the ban source; 9210 → 75 % plus `partial_ban` warning; extension filed 2026-11-30 and 2026-12-01 on a permit granted 2026-01-10 → `transition_maintenance_80`; filed 2026-12-02 → `salary_90`; 3511 transitional extension → 80 %, 30 640; extension filed 2026-11-30 on a permit granted 2026-07-10 → `salary_90`; first permit filed 2026-05-20, decided 2026-06-20 → 33 390; first permit decided 2026-05-31 → `out_of_scope`; extension filed 2026-05-31 → `out_of_scope`; declared `young_tech_company` on 2512 → 75 % naming the exemption; declared exemption on 5343 → `not_permitted`; salary exactly at threshold → pass
- [ ] T024 [P] [US1] `tests/unit/test_eligibility.py`, answer content: 80 % FTE gives a `part_time` warning citing the Migrationsverket employees page and an unchanged threshold; every warning has a source; a decision date of 2027-06-20 with no 2027 median gives a `stale_median` warning naming the latest median; every answer has a disclaimer mentioning collective agreements and "not legal advice"; `sources` holds the rule's row, the median's row and any code list or exemption used, each with `checked_on`
- [ ] T025 [P] [US1] `tests/integration/test_api.py`: `POST /api/v1/eligibility` returns the core answer for scenario 1; an invalid body returns 422 naming the field (`loc`); an unknown code returns 404 naming it

### Implementation

- [ ] T026 [US1] Implement `EligibilityRequest`, `EligibilityAnswer`, `Warning` and `evaluate()` in `src/lonekrav/core/eligibility.py`, following the rule-selection order in data-model.md and reading every date from registry rows (no legal date or amount literal in `eligibility.py`), until T022–T024 pass
- [ ] T027 [US1] Add `POST /eligibility` to `src/lonekrav/api/v1.py` (validate, call `evaluate`, return) until T025 passes
- [ ] T028 [US1] Run for real: `uv run lonekrav-serve`, curl every Story 1 scenario, compare each answer with the two Migrationsverket pages, and save the transcript as the first section of `references/api-smoke.md`

**Checkpoint**: MVP. Eligibility is usable over HTTP without any search.

---

## Phase 5: User Story 2 — find the plausible codes (P1)

**Goal**: fast and full search within the time budgets, title lists, legal flags on hits,
low-confidence note, honest-fit text.

**Independent test**: quickstart §3 search rows and §4 latency.

### Tests (write first, see them fail)

- [ ] T029 [P] [US2] `tests/unit/test_title_list.py`: `title_parts()` splits "Aktuarie/Försäkringsaktuarie/Försäkringsmatematiker" into three; "Game designer/Speldesigner" into two; returns None for prose with "/" ("we use and/or test. Then…"), for text with a line break, and when any part has more than six words (R4)
- [ ] T030 [P] [US2] `tests/integration/test_search_modes.py` on the fixture index: `SearchEngine` loads one dense matrix per model from the store and its top results equal `store.search_dense` for the same vector; `run(SearchRequest(mode="fast"))` reports `mode_used="fast"` and scores for kblab and bm25 only; `mode="full"` with an engine whose Harrier loader raises returns `mode_used="fast"` and a `fallback_reason`; a title-list query sets `title_list` and pools the parts' hits; every hit carries `legal_flags` (3511 has `exempt_75`); every answer carries `honest_fit`
- [ ] T031 [P] [US2] `tests/integration/test_search_modes.py`: hits are never ordered by threshold. For a fixed set of queries, the order equals the fused-score order, and the answer has no field derived from threshold (SC-007)
- [ ] T032 [P] [US2] `tests/integration/test_search_modes.py`: `low_confidence` is true when the top KBLab similarity is below the cut-off read from the benchmark results (inject a cut-off in the test)
- [ ] T033 [P] [US2] `tests/integration/test_api.py`: `POST /api/v1/search` returns a `SearchAnswer`; text longer than 20 000 characters, empty text and `k` = 21 return 422

### Implementation

- [ ] T034 [US2] In `src/lonekrav/core/embeddings.py`, add a `query_threads` setting to `Spec` (KBLab 1, Harrier unchanged) and apply it around `encode_queries` only, restoring the previous count afterwards (R2); test in `tests/unit/test_embeddings.py` that the count is 1 during a KBLab query and restored after. T040 measures Harrier at 1 thread and at the default and records both
- [ ] T035 [US2] Add `title_parts()` to `src/lonekrav/core/search.py` until T029 passes
- [ ] T036 [US2] Add `SearchEngine` (store, embedders, lazy Harrier loader, dense matrices loaded from the store (check the pymilvus 3 iterator API first; fall back to paged `query`), BM25 pool 50 for fast mode), `SearchRequest`, `SearchAnswer`, `run()`, `legal_flags` on `SearchHit` and the `HONEST_FIT` text to `src/lonekrav/core/search.py` until T030–T032 pass; keep `search()` as a thin wrapper so 001 callers still work
- [ ] T037 [US2] Make `evaluate` in `src/lonekrav/etl/benchmark.py` rank through the same engine code path as `run()` (title lists, pools, weights), so FR-017 holds; extend `tests/unit/test_metrics.py` with a check that `evaluate` and `run` give the same top five for one query on the fixture index
- [ ] T038 [US2] Derive the low-confidence cut-off in `src/lonekrav/etl/benchmark.py` per FR-017a, with `tests/eval/nonsense.yaml` (about 15 nonsense queries in both languages); write it into the results file; `SearchEngine` reads it at start-up
- [ ] T039 [US2] Add `POST /search` to `src/lonekrav/api/v1.py`; the app lifespan builds the real `SearchEngine` (T033)
- [ ] T040 [US2] Write `scripts/latency.py` (200 fast single-title queries, 50 full queries including 600-word ads, against a running server, reporting p50 and p95) and run it; fast p95 < 50 ms and full p95 < 1 s (SC-003). Save the output to `references/search-latency.md`. If the budget is missed, report the measured split before changing anything

**Checkpoint**: search usable over HTTP; latency recorded.

---

## Phase 6: User Story 5 — salary distribution (P2)

**Goal**: `GET /api/v1/occupations/{code}/salary` with official figures, threshold lines and the
optional simulated age block.

**Independent test**: quickstart §3 salary row; figures match SCB.

- [ ] T041 [P] [US5] `tests/unit/test_salary_payload.py` on fixture salary data: 2512's 2025 distribution matches the stored row exactly and names TAB5932 and 2025; threshold lines for 90 %, 75 % and the code's own rule on a given date come from the registry; a code with suppressed cells keeps nulls and lists them; `age_band="25-34"` gives percentiles equal to percentile × band mean ÷ all-ages mean, `is_simulated` true, the formula string and both input tables; a null input gives a null simulated value; a code with no salary rows sets `no_occupation_data`
- [ ] T042 [US5] Implement `ThresholdLine`, `SimulatedPercentiles`, `SalaryPayload` and `payload()` in `src/lonekrav/core/salary.py` until T041 passes
- [ ] T043 [US5] Add `GET /occupations/{code}/salary` (query `age_band`, `on`) to `src/lonekrav/api/v1.py` with a test in `tests/integration/test_api.py` (unknown code 404, bad age band 422)

---

## Phase 7: User Story 6 — compare candidate codes (P2)

**Goal**: `POST /api/v1/compare` with 2–5 codes side by side, honest-fit text.

**Independent test**: quickstart §3 compare rows.

- [ ] T044 [P] [US6] `tests/unit/test_compare.py` on fixture profiles: three codes come back in request order with Swedish descriptions (SCB MIS where present, else JobTech) and English descriptions (ESCO), each labelled with its source, latest salary, legal flags and threshold; with an offer each column has an eligibility answer equal to calling `evaluate` for that code; duplicates are dropped before counting; one code or six codes raise a validation error stating 2–5; `honest_fit` is present and no column is ordered or labelled by threshold
- [ ] T045 [US6] Implement `CompareRequest`, `CompareColumn`, `Comparison` and `compare()` in `src/lonekrav/core/compare.py` until T044 passes
- [ ] T046 [US6] Add `POST /compare` and `GET /occupations/{code}` (profile without ILO text) to `src/lonekrav/api/v1.py` with tests in `tests/integration/test_api.py`

---

## Phase 8: User Story 7 — legal timeline (P3)

**Goal**: `GET /api/v1/legal/timeline` and `GET /api/v1/benchmark`.

- [ ] T047 [P] [US7] `tests/integration/test_api.py`: the timeline route returns `registry.timeline()` with every event's source and `checked_on`; the benchmark route returns the results file, or 404 with a message when it is missing
- [ ] T048 [US7] Add both routes to `src/lonekrav/api/v1.py` until T047 passes

---

## Phase 9: User Story 4 — paste a whole job ad (P2)

**Goal**: `POST /api/v1/parse-job-ad` and `parse_ad` on search.

**Independent test**: quickstart §3 parse row; accuracy on the ad fixtures.

- [ ] T049 [P] [US4] Write five English and five Swedish made-up ads in `tests/fixtures/ads/*.txt`, each modelled on the structure of real Platsbanken ads (title line, company blurb, duties, requirements, benefits), with a hand label per passage in `tests/fixtures/ads/labels.yaml`
- [ ] T050 [P] [US4] `tests/unit/test_adparse.py`: the splitter yields one passage per line, bullet or sentence inside long lines; headings ("Om oss", "About us", "Arbetsuppgifter", "Responsibilities", "Kvalifikationer", "Requirements", "Vi erbjuder", "What we offer") label what follows and are not themselves kept; the first short line before any heading is `title` and kept; `keep` is true only for title, duty and skill; with a fake embedder and anchors, an un-headed passage takes the nearest anchor's label; an ad with nothing kept sets `fallback_to_whole`; parsing makes no network call (sockets blocked in the test, FR-022)
- [ ] T051 [US4] Implement `src/lonekrav/core/adparse.py` and `src/lonekrav/core/adparse_anchors.yaml` (a few anchor sentences per label and language) until T050 passes
- [ ] T052 [US4] `tests/integration/test_search_modes.py`: `parse_ad=True` searches the kept text, returns `passages` and `searched_text`, and falls back to the whole ad when nothing is kept; implement in `run()` in `src/lonekrav/core/search.py`
- [ ] T053 [US4] Add `POST /parse-job-ad` to `src/lonekrav/api/v1.py` with a test in `tests/integration/test_api.py`
- [ ] T054 [US4] `tests/eval/test_adparse_accuracy.py` (benchmark marker, real KBLab): passage label agreement ≥ 85 % on the ten ads, and search on kept text puts the expected code in the top five at least as often as on the raw ad (SC-005). Run it and record the result. Real JobTech ads replace the made-up ones only after the licence is confirmed (research R5); until then SC-005 stays open and the PR says so

---

## Phase 10: Polish & cross-cutting

- [ ] T055 [P] Write `scripts/api_smoke.py`: calls every route in contracts/api-v1.md once with made-up offers and public example text, and writes requests and responses as markdown; run it against `lonekrav-serve` into `references/api-smoke.md` (SC-008, SC-001)
- [ ] T056 [P] Test in `tests/unit/test_legal.py` (SC-002): no median amount, threshold amount, rule percentage or rule date from the registry appears in `src/` outside `legal_constants.yaml`, found by loading the registry and searching each `.py` file for each value (amounts with and without a thousands space; dates in ISO form)
- [ ] T057 [P] Measure peak memory of the running server after one full-mode request with both models loaded and add it to `references/embedding-benchmark.md` (plan constraint: 4 GB)
- [ ] T058 [P] Write `docs/walkthroughs/002-search-eligibility-api.md` with the walkthrough skill (snippets emitted from disk)
- [ ] T059 [P] Compound step: add the leak rule, the in-memory dense search finding and the one-thread encoding finding to `CLAUDE.md`; update `references/benchmark-fusion-diagnostic.txt` (outdated since 001) or delete it in favour of `references/benchmark-diagnosis-002.md`
- [ ] T060 Final gate: `uv run ruff check .`, `uv run pytest`, `uv run pytest -m benchmark` all green; then open the PR for `002-search-eligibility-api` with the evidence from T017, T020, T028, T040, T054, T055 and T057

---

## Dependencies & Execution Order

- Setup (T001–T002) → Foundational (T003–T010) → US3 diagnosis and fusion (T011–T021) → US1 (T022–T028) → US2 (T029–T040) → US5, US6, US7 (in parallel) → US4 → Polish.
- US1 needs only the registry; it can start in parallel with US3 if someone else takes it.
- US3's gate tests (T021) are confirmed only after US2 (T037 makes the benchmark use the live search path), in T060.
- US6 needs US1 (eligibility per column) and US5 (salary summary).
- US4 needs US2 (search `run()`).
- Within a story: tests → see red → implementation → green → real run.

## Parallel Examples

- Foundational: T003 and T008 are independent test files.
- US3: T011, T013, T015 and T018 are independent tests.
- US1: T022–T025 are separate test groups; T022–T024 share a file, so write them in sequence.
- US2: T029–T033 can be written together; T034 and T035 touch different files.
- After US2: US5 (T041–T043), US7 (T047–T048) and the ad fixtures (T049) in parallel.
- Polish: T055–T059 in parallel.

## Implementation Strategy

1. **MVP = Foundational + US1**: a working, sourced eligibility check over HTTP. It is useful on
   its own and is what 003's MCP tool and 004's calculator need first.
2. US3 runs before US1 in the order above because its findings can change search; if the
   diagnosis is quick, US1 can be finished first without harm.
3. Add US2 (search), then US5–US7 (read-only views), then US4 (ad parsing).
4. Polish, final gate, PR. If the PR grows too large, split it at the checkpoints: registry +
   eligibility; benchmark + search; payloads + compare + timeline; ad parsing.
