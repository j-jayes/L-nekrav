# Implementation Plan: Occupation Search, Permit Eligibility and Salary API

**Branch**: `002-search-eligibility-api` | **Date**: 2026-10-21 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-search-eligibility-api/spec.md`

## Summary

Add a legal registry and an eligibility engine, a faster two-mode search that also handles
slash-joined titles and pasted ads, salary payloads and code comparison, and serve all of it as a
versioned FastAPI app. Research changed two things. First, the Swedish search gap is mostly a
benchmark artefact (104 of 111 English generated queries leak into the index through plurals),
plus Swedish BM25 pulling the equal-weight fusion down; the dense models are already equal across
languages (R1). Second, Migrationsverket keys the new rule on the decision date, and transitional
extensions use the old 80 % maintenance requirement with no 75 % exemption (R6). Both corrections
are now in the spec.

## Technical Context

**Language/Version**: Python 3.12 (uv-managed)

**Primary Dependencies**: 001's stack (pydantic 2, pymilvus 3 with milvus-lite, sentence-transformers
6, polars, pyyaml, snowballstemmer) plus `fastapi` and `uvicorn`

**Storage**: committed `src/lonekrav/core/legal_constants.yaml` (new); 001's committed
`data/processed/` files; the gitignored Milvus Lite index; dense vectors held in memory at runtime
(≈ 68 MB, R2)

**Testing**: pytest. Default run offline with the FakeEmbedder and fixtures, including FastAPI
`TestClient` tests. `-m benchmark` runs real models and both modes.

**Target Platform**: macOS arm64 (dev) and Linux (container, Feature 004)

**Project Type**: Python library plus web service

**Performance Goals**: fast search p95 < 50 ms (measured path ≈ 43 ms, R2); full search p95 < 1 s
including a 600-word ad (R3)

**Constraints**: 4 GB memory budget (Harrier ≈ 3.1 GB and KBLab ≈ 0.7 GB, measured separately in 001; measure together in this feature); no LLM; no network at
request time; no request contents in logs

**Scale/Scope**: single user to a few concurrent users; 429 occupations, 9 556 chunks; 9 routes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | How |
|---|---|---|
| I. Core first, adapters thin | Pass | Eligibility, registry, search engine, parsing, payloads and comparison are core modules with core models; `api/v1.py` only validates, calls core and returns the model. |
| II. Data integrity | Pass | Thresholds only in `legal_constants.yaml`, each row with dates, source and checked-on; amounts derived and tested against Migrationsverket's table; simulated age figures flagged with formula and inputs, null in → null out. |
| III. Honest fit | Pass | Honest-fit text on search, comparison and eligibility; no sort-by-threshold anywhere (SC-007 test); every legal statement carries a source and checked-on date; disclaimer on every eligibility answer. |
| IV. Test-first, proven by hand | Pass | TDD per task; the boundary cases in quickstart §3 become tests first; the benchmark gate covers both modes; `references/api-smoke.md` and latency output go in the PR. |
| V. Compact and portable | Pass | Dense matrix loaded from the store, so `MILVUS_URI` still works; memory stays within the 4 GB budget; no key needed. |
| VI. Simplicity | Pass | No content logging (FR-033 allows it, nothing needs it); no threading; ONNX and trained classifiers rejected; fusion fix tried in order of simplicity (R1). |

Post-design re-check: still passing. The registry moves from Python constants to YAML; that is a
change of form, not an extra layer, and it is what Principle II and the yearly update need (R6).

## Project Structure

### Documentation (this feature)

```text
specs/002-search-eligibility-api/
├── spec.md  plan.md  research.md  data-model.md  quickstart.md
├── contracts/api-v1.md
├── checklists/requirements.md
└── tasks.md                     # /speckit-tasks
```

### Source Code (repository root)

```text
src/lonekrav/
├── core/
│   ├── legal_constants.yaml  # NEW: medians, rules, code lists, exemptions, sources
│   ├── legal.py              # NEW: registry models, load + validate, median_on, timeline
│   ├── legal_flags.py        # CHANGED: reads code sets from the registry; same flags_for()
│   ├── eligibility.py        # NEW: EligibilityRequest/Answer, evaluate()
│   ├── search.py             # CHANGED: SearchEngine (dense matrices), modes, title lists,
│   │                         #          weighted fusion, low-confidence, SearchRequest/Answer
│   ├── adparse.py            # NEW: split, heading lexicon, anchor centroids, ParsedAd
│   ├── adparse_anchors.yaml  # NEW: anchor sentences per label and language
│   ├── salary.py             # CHANGED: SalaryPayload, ThresholdLine, simulated percentiles
│   └── compare.py            # NEW: CompareRequest, Comparison
├── api/
│   └── v1.py                 # NEW: the nine routes
├── app.py                    # NEW: create_app(), lifespan loads SearchEngine; main() for lonekrav-serve
└── etl/
    └── benchmark.py          # CHANGED: inflection-aware leak check, modes, diagnosis, previous results

scripts/
├── api_smoke.py              # NEW: every route once → references/api-smoke.md
└── latency.py                # NEW: p50/p95 for fast and full against a running server

tests/
├── unit/                     # test_legal, test_eligibility, test_adparse, test_title_list,
│                             # test_salary_payload, test_compare, test_leak_check
├── integration/              # test_api (TestClient over the fixture index), test_search_modes
├── fixtures/ads/             # made-up ads now; real JobTech ads once the licence is confirmed
└── eval/                     # test_benchmark (both modes), nonsense.yaml, test_adparse_accuracy
```

**Structure Decision**: same single package; `api/` and `app.py` arrive as the constitution layout
foresaw. `protocols/` stays for Feature 003.

## Implementation order (for /speckit-tasks)

1. **Benchmark diagnosis first** (R1, Story 3). It gates the merge and could change the search
   design, so it comes before any search code: save 001 results; inflection-aware leak check
   (TDD); rebuild; diagnosis table; then fusion weights and, only if needed, analyser changes.
2. **Legal registry and eligibility** (Story 1): YAML + models + validation against the published
   table, then each rule-selection step red/green from the scenarios, then `legal_flags` reads the
   registry.
3. **Search engine** (Story 2): dense matrices, one-thread encoding, pool 50, modes and fallback,
   title lists (R4), legal flags on hits, low-confidence cut-off; benchmark calls the same code.
4. **API skeleton** with eligibility and search routes, TestClient tests, `lonekrav-serve`, first
   smoke run and latency run.
5. **Salary payload** (Story 5), **comparison** (Story 6), **timeline, occupation, benchmark and
   health routes** (Story 7).
6. **Ad parsing** (Story 4): splitter and headings, anchors, title rule, `parse_ad` in search,
   accuracy check on made-up ads; real ads when the licence is confirmed.
7. Smoke transcript, latency evidence, walkthrough in `docs/walkthroughs/`, compound step
   (reference the latency findings and the leak check in `CLAUDE.md`).

## Complexity Tracking

No violations.
