---
description: "Task list for Feature 001: SSYK occupation dataset and bilingual search index"
---

# Tasks: SSYK Occupation Dataset and Bilingual Search Index

**Input**: `specs/001-data-taxonomy-index/` (plan.md, spec.md, research.md, data-model.md,
contracts/cli.md, quickstart.md)

**Tests**: Required. Constitution Principle IV mandates red/green TDD. Every test task MUST be run
and seen to fail for the stated reason before its implementation task starts.

**Fixtures**: Tests run on small slices of real downloads saved under `tests/fixtures/` (cut with a
script, never hand-typed). The default `uv run pytest` is offline. Real models only run under
`-m benchmark`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1–US5 from spec.md

---

## Phase 1: Setup

- [X] T001 Add runtime dependencies to `pyproject.toml` with `uv add` (httpx, pydantic, openpyxl, pypdf, polars, pyyaml, `pymilvus[milvus-lite]>=3`, `sentence-transformers>=6`, psutil); register `lonekrav-etl = "lonekrav.etl.cli:main"`; remove the `uv init` placeholder `main` from `src/lonekrav/__init__.py` and its `lonekrav` script entry
- [X] T002 Configure pytest in `pyproject.toml`: `testpaths = ["tests"]`, a `benchmark` marker, and `addopts = "-m 'not benchmark'"`; configure ruff (line length 100)
- [X] T003 [P] Create the package skeleton `src/lonekrav/core/__init__.py`, `src/lonekrav/etl/__init__.py` and the folders `tests/unit/`, `tests/integration/`, `tests/eval/`, `tests/fixtures/`, `data/processed/`
- [X] T004 [P] Write `scripts/cut_fixtures.py`, a standalone script using plain httpx and openpyxl that downloads each source once and keeps only slices for the codes 0000, 0110, 1211, 1212, 2512, 2421, 3511, 4430, 5322, 5343 and 9210: workbook rows re-saved as small xlsx, json-stat2 responses filtered to those codes, GraphQL responses, ILO rows, a few ESCO URIs, and the PDF text pages. It writes them to `tests/fixtures/`. Run it, read the output, and commit the fixtures, so parser tests have real inputs before any parser exists.

---

## Phase 2: Foundational (blocks every story)

- [X] T005 [P] Test `tests/unit/test_models.py`: OccupationProfile requires a 4-digit code, `title_sv`, `title_en` and at least one Swedish description; Synonym deduplicates on (lang, casefolded label); SalaryDistribution rejects `p10 > p25` and lists null fields in `suppressed`
- [X] T006 Implement the pydantic models from data-model.md in `src/lonekrav/core/models.py` until T005 passes
- [X] T007 [P] Test `tests/unit/test_http.py` with an httpx MockTransport: download writes `<file>` and `<file>.meta.json` (url, fetched_at, sha256); a cached file is reused without `force`; a failed download (simulated with the mock transport returning a connection error and a 500) raises an error naming the source and URL, and leaves the old file untouched
- [X] T008 Implement the cached atomic download in `src/lonekrav/etl/http.py` (temporary file, then rename) until T007 passes
- [X] T009 [P] Test `tests/unit/test_cli.py`: `lonekrav-etl --help` lists fetch, build, index, benchmark and measure-models; an unknown source for `fetch --only` exits 1 with a message
- [X] T010 Implement the argparse skeleton in `src/lonekrav/etl/cli.py`, with subcommands calling stub functions, until T009 passes
- [X] T011 Check the fixtures from T004 against the live sources: for each fixture, record its URL and fetch date in `tests/fixtures/README.md`

---

## Phase 3: User Story 1 — complete, trustworthy occupation profile (P1) 🎯 MVP

**Goal**: 429 profiles with official titles, descriptions, synonyms, ISCO and ESCO links, legal flags,
and a discrepancy report.

**Independent test**: `lonekrav-etl build`, then quickstart checks 1–4.

### Tests (write first, see them fail)

- [X] T012 [P] [US1] `tests/unit/test_legal_flags.py`: exactly 27 `exempt_75` codes equal to the SFS 2026:605 list; 5343 is `banned`; 9210 has both `exempt_75` and `partially_banned`; every flag cites `SFS 2026:605` with effective_from 2026-06-01
- [X] T013 [P] [US1] `tests/unit/test_scb_files.py` on fixtures: the structure workbook gives 426 codes; the English workbook gives "Software- and system developers" for 2512; the ISCO key splits "2511, 2512, 2513, 2514, 2521" for 2512; title-index rows with 3-digit codes are dropped
- [X] T014 [P] [US1] `tests/unit/test_jobtech.py` on GraphQL fixtures: parse ssyk-level-4 definitions and occupation-names with alternative labels and ESCO matches (match type kept); map merged code 1210 to 1211 and 1212 with `jobtech_shared=True`
- [X] T015 [P] [US1] `tests/unit/test_ilo.py` on fixture rows: 2512 gives an English definition, a tasks text and included-occupation titles ("Software engineer" and others), each tagged `isco_code="2512"`
- [X] T016 [P] [US1] `tests/unit/test_esco.py` on fixture JSON: one occupation URI gives en and sv preferred labels, alternative labels and descriptions
- [X] T017 [P] [US1] `tests/unit/test_mis2012.py` on fixture PDF text: descriptions for 1212, 4430 and 5322 are extracted from the description section, not from the overview list or correspondence tables (assert that the text for 1212 starts "Verksamhetsnära chef")
- [X] T018 [US1] `tests/integration/test_build_profiles.py`: building from fixtures gives profiles for every fixture code. 0110 gets its title from the salary-table label and its English title from ILO; 2512 has no flags, at least one sv and one en description, and synonyms in both languages; the discrepancy rows for 0110 and 1212 are correct; a fixture code with no ESCO or ILO text still builds from the SCB/JobTech text and records the absence in `sources`; output JSON is sorted and two builds are byte-identical

### Implementation

- [X] T019 [P] [US1] `src/lonekrav/core/legal_flags.py`: code lists as data with the SFS citation (T012)
- [X] T020 [P] [US1] `src/lonekrav/etl/scb_files.py`: download and parse the four SCB workbooks (T013)
- [X] T021 [P] [US1] `src/lonekrav/etl/jobtech.py`: GraphQL fetch with paging and the parsers (T014)
- [X] T022 [P] [US1] `src/lonekrav/etl/ilo.py` (T015)
- [X] T023 [P] [US1] `src/lonekrav/etl/esco.py`: fetch per URI for en and sv, cached under `data/raw/esco/`, polite rate limit (T016)
- [X] T024 [P] [US1] `src/lonekrav/etl/mis2012.py`: description-section parser used only for gap codes (T017)
- [X] T025 [US1] `src/lonekrav/core/profiles.py`: assemble profiles from parsed sources with source precedence (SCB, then JobTech, ILO, ESCO), synonym dedup, and `load_profiles()`; write `ssyk_profiles.json` and `discrepancies.csv` (T018)
- [X] T026 [US1] Wire `fetch` (scb_files, jobtech, ilo, esco, mis2012) and the profile half of `build` into `src/lonekrav/etl/cli.py`
- [X] T027 [US1] Run for real: `lonekrav-etl fetch && lonekrav-etl build`, then quickstart checks 1–4. Paste the output into the PR notes. Any bug found becomes a failing test first.

---

## Phase 4: User Story 2 — official salary statistics (P1)

**Goal**: salary distributions and age-band means, 2014–2025, nothing imputed.

**Independent test**: quickstart checks 5–9.

### Tests

- [X] T028 [P] [US2] `tests/unit/test_scb_pxweb.py` on json-stat2 fixtures: TAB5932 2025 gives 0000 a median of 38 300 and 2512 the values mean 55 500, median 53 500, P10 39 600, P25 46 200, P75 62 600, P90 72 600 with CI half-widths; TAB4265 gives null CIs; null cells end up in `suppressed`
- [X] T029 [P] [US2] `tests/unit/test_salary_age.py`: TAB5844 2025 for 2512 gives 18–24 mean 36 100 with headcount null and suppressed; the 65–66 band is dropped; TAB4264 rows have `source_table="TAB4264"`
- [X] T030 [US2] `tests/integration/test_build_salary.py`: each (code, year) appears once; years 2014–2022 come from TAB4265 and 2023 onwards from TAB5932; every row has source_table, reference_year and a `fetched_at` equal to the raw file's meta; a percentile-order violation fails the build with the code and year in the message

### Implementation

- [X] T031 [US2] `src/lonekrav/etl/scb_pxweb.py`: GET json-stat2 for TAB4265, TAB5932, TAB4264 and TAB5844 with Sektor=0 and Kon=1+2, all codes and years (T028)
- [X] T032 [US2] `src/lonekrav/core/salary.py`: json-stat2 to SalaryDistribution and AgeBandSalary, validation, `load_distributions()` and `load_age_bands()`; write the parquet files (T029, T030)
- [X] T033 [US2] Wire `fetch --only scb_pxweb` and the salary half of `build` into the CLI
- [X] T034 [US2] Run for real: quickstart checks 5–8, then check 9 by comparing 10 codes against statistikdatabasen.scb.se by hand (record the codes and URLs in the PR)

---

## Phase 5: User Story 3 — find the right occupation in any language (P2)

**Goal**: portable index; per-method and fused rankings.

**Independent test**: quickstart checks 11–13.

### Tests

- [X] T035 [P] [US3] `tests/unit/test_chunks.py`: a profile yields title, desc_sv, desc_en and synonym chunks of at most 2 000 characters and at most 40 labels; hold-out titles (and the alternative labels of the same occupation-name) are absent from every chunk
- [X] T036 [P] [US3] `tests/unit/test_embeddings.py`: FakeEmbedder is deterministic and L2-normalised; the registry returns `kblab` and `harrier` specs with the right dims; harrier specifies fp32 and the `web_search_query` prompt for queries only (no model load)
- [X] T037 [P] [US3] `tests/unit/test_fusion.py`: chunk hits reduce to one max score per code; BM25 distances are sign-flipped so higher is better; RRF with k=60 on known ranks gives the expected order; a code missing from one method gets `None` for that score
- [X] T038 [US3] `tests/integration/test_index_search.py` with FakeEmbedder and a temp Milvus Lite file: index the fixture profiles; "mjukvaruutvecklare" ranks 2512 first under bm25; the fused hit carries all three score fields and the matched chunk; deleting and rebuilding gives the same results

### Implementation

- [X] T039 [P] [US3] `src/lonekrav/core/chunks.py` (T035)
- [X] T040 [P] [US3] `src/lonekrav/core/embeddings.py`: Embedder protocol, FakeEmbedder, and lazily loaded KBLab and Harrier (fp32, prompts) (T036)
- [X] T041 [US3] `src/lonekrav/core/store.py`: the collection schema from `references/milvus_lite_hybrid.py`, batch insert, per-method search, and `MILVUS_URI` override
- [X] T042 [US3] `src/lonekrav/core/search.py`: reduce, flip BM25, RRF, SearchHit (T037, T038)
- [X] T043 [US3] Wire `index` into the CLI
- [X] T044 [US3] Run for real with both models: `lonekrav-etl index`, then quickstart checks 11–13; record index size and build time

---

## Phase 6: User Story 4 — prove language does not change results (P2)

**Goal**: benchmark file and gate.

**Independent test**: quickstart check 14.

### Tests

- [X] T045 [P] [US4] `tests/unit/test_metrics.py`: Recall@1, Recall@5 and MRR on hand-computed toy rankings, including several acceptable codes per query and a missed query (reciprocal rank 0)
- [X] T046 [P] [US4] `tests/unit/test_generated_set.py`: the seeded sample is stable across runs, has at most one query per code and at least 200 queries; the English text comes from ESCO exact or close matches only; the hold-out file lists every sampled title
- [X] T047 [P] [US4] `tests/unit/test_handwritten_queries.py`: the YAML parses into BenchmarkQuery; at least 30 queries; every type present; every expected code exists in the profiles

### Implementation

- [X] T048 [US4] Write `tests/eval/queries_handwritten.yaml`: 30+ EN/SV pairs, including the look-alikes 2512/2511/2514, 2122 statistician/2421/2512 data analyst, 2221–2229 nurse specialities, and manager nivå 1/2 pairs. Flag it for review by a Swedish speaker in the PR. (T047)
- [X] T049 [US4] `src/lonekrav/etl/benchmark.py`: the generated set and hold-out (written during `build`), metrics, results JSON with model ids and revisions (T045, T046)
- [X] T050 [US4] `tests/eval/test_benchmark.py`, marked `benchmark`: loads the real index, asserts SC-004 (fused Recall@5 ≥ 0.80 per language), SC-005 (gap ≤ 5 points) and SC-006 (fused ≥ each method), and that for at least 80 % of the hand-written pairs the English and Swedish fused top-five lists share at least three codes (spec Story 3, scenario 2)
- [X] T051 [US4] Wire `benchmark` into the CLI; run `lonekrav-etl benchmark` and `uv run pytest -m benchmark` for real; commit `data/processed/benchmark_results.json`. If a gate fails, report it with the numbers rather than loosening the threshold.

---

## Phase 7: User Story 5 — repeatable rebuild (P3)

**Goal**: idempotent four-step pipeline, measured models, no LLM.

**Independent test**: quickstart checks 10, 11 and 15.

- [X] T052 [P] [US5] `tests/unit/test_measure.py`: the measurement writer renders the markdown table from a dict of fake results
- [X] T053 [US5] `src/lonekrav/etl/measure.py` plus the `measure-models` subcommand: run each model fp32 (and Harrier bf16 for comparison) and regenerate `references/embedding-benchmark.md` (T052)
- [X] T054 [US5] `tests/integration/test_idempotent.py`: build twice from fixtures gives byte-identical files; build with `OPENROUTER_KEY` unset succeeds
- [X] T055 [US5] Run for real: delete `data/processed/*` and the index, run all steps, time each one against SC-007, and run quickstart checks 10 and 11

---

## Phase 8: Polish

- [X] T056 Write `data/processed/data-dict.yaml` with the data-dict skill: profile it, interview the maintainer on anything guessed, record the licence and attribution for SCB, JobTech, ILO and ESCO (confirm the ESCO wording), and validate against the real files
- [X] T057 [P] Write `docs/walkthroughs/001-data-pipeline.md` with the walkthrough skill (snippets emitted with sed, never retyped)
- [X] T058 [P] Compound step: update `CLAUDE.md` (bf16 gotcha, fixture workflow) and `references/` with any trick worked out; tick the tasks in this file
- [ ] T059 Run `uv run ruff check .`, `uv run pytest` and `uv run pytest -m benchmark`; open the PR for `001-data-taxonomy-index` with the evidence from T027, T034, T044, T051 and T055

---

## Dependencies & Execution Order

- Setup (T001–T004) → Foundational (T005–T011) → US1 and US2 in parallel → US3 → US4 → US5 → Polish.
- Fixtures come from the standalone T004 script, so parser tests have real inputs first. US2 does not depend on US1.
- US3 needs US1 profiles. US4 needs US3. US5 hardens all of them.
- Within a story: tests → see red → implementation → green → real run.

## Parallel Examples

- US1: T012–T017 are six independent test files; T019–T024 are six independent modules.
- US3: T035, T036 and T037 in parallel; T039 and T040 in parallel.
- US4: T045, T046 and T047 in parallel.

## Implementation Strategy

1. **MVP = US1 + US2** (profiles and salary). That is already useful to Feature 002's eligibility
   logic, without search.
2. Add US3, demo spot queries.
3. Add US4, publish the benchmark.
4. US5 and Polish, then the PR.
