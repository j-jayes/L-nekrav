# Implementation Plan: Occupation map

**Branch**: `007-occupation-map` (built on `006-your-number`) | **Date**: 2026-10-27 | **Spec**: [spec.md](spec.md)

## Summary

`lonekrav-etl map` pools the cached Harrier vectors of each code's title and description chunks
(ILO excluded) into one vector. From those it computes exact cosine neighbours and the
distribution of pair similarities, and runs UMAP once with a fixed seed. It writes two committed
artefacts: `occupation_map.json` (points, neighbours and parameters) and
`occupation_similarity.parquet` (every pair).

Serving reads only those files: `GET /map`, `/occupations/{code}/neighbours`, `/closeness`, and two
MCP tools. The page gets an `OccupationMap` SVG component next to the search results, and
"Similar work" on each 006 card. Research R1–R3 measured the approach on the real cache: it gives
sensible neighbours and 65 % neighbour preservation in 2-D.

## Technical Context

- **Language/Version**: Python 3.12 (uv); TypeScript 5.9.
- **Primary Dependencies**: `umap-learn` in a new uv group, `map`, which is never installed in the
  image (R4). numpy and polars are already present.
- **Storage**: about 60 KB of JSON and about 400 KB of Parquet in `data/processed/`. No change to
  Milvus.
- **Testing**:
  - pytest for pooling (fake vectors, ILO and synonym exclusion), neighbours, quantiles,
    same-description labelling, the artefact schema, the routes, the MCP tools and drift;
  - one UMAP test under `importorskip`;
  - Vitest for the map component and its placement;
  - Playwright screenshots and axe.
- **Performance Goals**: `/map` answers in under 50 ms. Hover takes under 16 ms per frame with a
  4× CPU throttle (SC-004).
- **Constraints**:
  - no text in the artefacts;
  - no pay colour;
  - neighbours never ordered by pay;
  - the image grows by under 1 MB (SC-006).
- **Scale**: 429 points; 91 806 pairs.

## Constitution Check

| Principle | Check | Status |
|---|---|---|
| I. Core first | Pooling, neighbours and closeness live in core (`core/occupation_map.py`). The ETL step only wires the cache and UMAP. The surfaces only call `Service`. | Pass |
| II. Data integrity | No SCB figure is derived. Medians in neighbour answers are copied with their year. The artefacts are documented in `data-dict.yaml`, with provenance and parameters. | Pass |
| III. Honest fit | Every answer carries `HONEST_FIT`. Colour is by group, never by pay. The caption says similar descriptions never decide the code. | Pass |
| IV. Test-first | Red/green per task. Evidence: curl, screenshots and the SC-003 figure. | Pass |
| V. Compact | Only the JSON and Parquet files ship. umap and numba stay out of the image (checked in quickstart). | Pass |
| VI. Simplicity | Hand-drawn SVG, no chart or zoom library. One ETL subcommand. | Pass |
| ILO rule | ILO chunks are excluded from pooling, and the artefact holds no text. | Pass |

## Project Structure

```text
src/lonekrav/core/occupation_map.py      # NEW: pool(), neighbours(), quantiles(), closeness(), load()
src/lonekrav/etl/occupation_map.py       # NEW: read the Harrier cache, call core, run UMAP, write
src/lonekrav/etl/cli.py                  # + "map" subcommand
src/lonekrav/core/service.py             # + map, similarity; neighbours(), closeness()
src/lonekrav/api/v1.py                   # + /map, /occupations/{code}/neighbours, /closeness
src/lonekrav/protocols/mcp_server.py     # + get_similar_occupations, get_occupation_closeness
src/lonekrav/app.py                      # load the artefacts; stale check against SPECS["harrier"]
data/processed/occupation_map.json, occupation_similarity.parquet, data-dict.yaml
frontend/src/components/OccupationMap.tsx (+ test)
frontend/src/lib/mapScale.ts (+ test)    # viewBox zoom/pan, nearest-point lookup
frontend/src/views/SearchView.tsx        # two-column layout with the map
frontend/src/views/NumberView.tsx        # "Similar work", pair closeness
tests/unit/test_occupation_map.py; tests/integration/test_map_api.py; test_mcp.py; test_openapi_drift.py
references/occupation_map_probe.py, references/occupation-map.md
pyproject.toml                           # [dependency-groups] map
```

## Complexity Tracking

None.
