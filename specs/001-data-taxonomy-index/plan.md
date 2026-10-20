# Implementation Plan: SSYK Occupation Dataset and Bilingual Search Index

**Branch**: `001-data-taxonomy-index` | **Date**: 2026-10-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-data-taxonomy-index/spec.md`

## Summary

Build 429 canonical SSYK 2012 occupation profiles from official Swedish and international sources,
official SCB salary distributions and age-band means for 2014–2025, a chunked Milvus Lite index with
two dense models and BM25, and a cross-lingual benchmark. Everything comes from a four-step CLI that
needs no LLM. Fusion happens in core after reducing chunk scores to occupation scores (research R7).
LLM enrichment is deferred (R6).

## Technical Context

**Language/Version**: Python 3.12 (uv-managed)

**Primary Dependencies**: httpx, pydantic 2, openpyxl, pypdf, polars, pyyaml, pymilvus 3 with
milvus-lite 3.2, sentence-transformers 6 (torch CPU)

**Storage**: committed JSON, Parquet and CSV in `data/processed/`; Milvus Lite file
`data/lonekrav_milvus.db` (gitignored, rebuilt); raw cache in `data/raw/` (gitignored)

**Testing**: pytest. Default run is offline with a fake embedder and fixtures in `tests/fixtures/`;
`-m benchmark` runs the real models.

**Target Platform**: macOS arm64 (dev, M2 Pro 16 GB) and Linux x86_64 or arm64 (container)

**Project Type**: Python library plus CLI (data pipeline)

**Performance Goals**: full rebuild in under 60 minutes, rebuild from cache in under 15; the fused
search latency is measured here and budgeted in Feature 002

**Constraints**: index under 200 MB; 4 GB container memory budget, decided 2026-10-20 after measurement (R8);
no network or models in the default test run

**Scale/Scope**: 429 occupations, about 3 000–5 000 chunks, about 12 years × 430 salary rows, about
30 + 200 benchmark queries

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | How |
|---|---|---|
| I. Core first, adapters thin | Pass | All models and logic in `core/`. `etl/` is I/O and parsing only, and calls core builders. No transport frameworks in this feature. |
| II. Data integrity | Pass | Nulls kept with a `suppressed` list; `source_table`, `reference_year` and `fetched_at` on every row; percentile ordering validated rather than fixed; legal flags cite SFS 2026:605; every source in `data-dict.yaml`. |
| III. Honest fit | Pass (n/a) | No user-facing advice in this feature. Legal flags carry citations for later copy. |
| IV. Test-first, proven by hand | Pass | TDD per task against fixture slices of real downloads; quickstart checks 1–15 run by hand with output in the PR; benchmark gate via `-m benchmark`. |
| V. Compact and portable | Pass | Single Milvus Lite file rebuilt from committed data; memory measured first (R8); no LLM. |
| VI. Simplicity | Pass | LLM enrichment deferred; one collection; fusion in about ten lines rather than a framework; no plugin system for sources. |

Post-design re-check: still passing. The one deliberate deviation from the user's plan input (core
fusion instead of `RRFRanker`) is justified in R7 and makes the design simpler, not more complex.

## Project Structure

### Documentation (this feature)

```text
specs/001-data-taxonomy-index/
├── spec.md  plan.md  research.md  data-model.md  quickstart.md
├── contracts/cli.md
├── checklists/requirements.md
└── tasks.md                     # /speckit-tasks
```

### Source Code (repository root)

```text
src/lonekrav/
├── core/
│   ├── models.py          # pydantic models from data-model.md
│   ├── legal_flags.py     # SFS 2026:605 code lists + citation
│   ├── profiles.py        # assemble + load OccupationProfile
│   ├── salary.py          # json-stat2 → SalaryDistribution / AgeBandSalary, validation, load
│   ├── chunks.py          # profile → chunks, hold-out removal
│   ├── embeddings.py      # Embedder protocol, kblab, harrier, FakeEmbedder
│   ├── store.py           # Milvus Lite schema, insert, per-method search
│   └── search.py          # reduce chunk→code, RRF fuse, SearchHit
└── etl/
    ├── cli.py             # lonekrav-etl
    ├── http.py            # cached atomic download + .meta.json
    ├── scb_files.py       # four xlsx workbooks
    ├── scb_pxweb.py       # TAB4265, TAB5932, TAB4264, TAB5844
    ├── mis2012.py         # description section parser (gap codes)
    ├── jobtech.py         # GraphQL ssyk-level-4, occupation-name, esco matches
    ├── ilo.py             # ISCO-08 EN definitions
    ├── esco.py            # occupation fetch en+sv by URI
    ├── benchmark.py       # generated set, metrics, results file
    └── measure.py         # model latency + memory → references/

tests/
├── fixtures/              # small real slices: xlsx rows, json-stat2, GraphQL, PDF pages
├── unit/                  # one file per core/etl module
├── integration/           # build on fixtures → profiles; index + search with FakeEmbedder
└── eval/
    ├── queries_handwritten.yaml
    └── test_benchmark.py  # @pytest.mark.benchmark

data/processed/            # committed outputs + data-dict.yaml
references/                # milvus_lite_hybrid.py (spike), embedding-benchmark.md
```

**Structure Decision**: single Python package with `core/` and `etl/` subpackages, matching the
constitution layout. `api/` and `protocols/` arrive in Features 002 and 003.

## Implementation order (for /speckit-tasks)

1. **Model measurement first** (R8). This is the only finding that could change the design, so it
   comes before any pipeline code.
2. Models and legal flags (pure core, TDD).
3. Cached HTTP plus each source parser against fixtures (TDD), then `fetch`.
4. Salary parsing and validation, then profile assembly and discrepancies, then `build`.
5. Chunks, embeddings, store and search with FakeEmbedder (TDD), then `index`.
6. Hand-written queries, generated set and hold-out, metrics, then `benchmark` and the gate.
7. Data dictionary (data-dict skill, interview the maintainer), quickstart run, walkthrough.

## Complexity Tracking

No violations.
