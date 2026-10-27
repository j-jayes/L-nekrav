# Tasks: Occupation map

**Prerequisites**: Feature 006 merged; plan.md, research.md, data-model.md, contracts/.
**Tests**: red/green (Constitution IV).

## Phase 1: Setup

- [ ] T001 Move the probe scripts to `references/occupation_map_probe.py` (pooling, neighbours, UMAP preservation) with its measured output in the docstring
- [ ] T002 Add `[dependency-groups] map = ["umap-learn"]` to `pyproject.toml` (a version at least two weeks old), `uv lock`, and confirm `uv sync --no-dev` does not install it

## Phase 2: User Story 1 — How close are two occupations? (P1) 🎯 MVP

- [ ] T003 [US1] Write failing tests in `tests/unit/test_occupation_map.py` with fake profiles and vectors: `pool()` uses only title/desc chunks with `ilo=False` and normalises; `neighbours()` gives the top k by cosine and excludes self; `quantiles()` gives 101 sorted values; `closeness()` gives the percentile to a whole per cent, and `same_description` at ≥ 0.99 with a null percentile
- [ ] T004 [US1] Implement `src/lonekrav/core/occupation_map.py` (models from data-model.md, pure functions, load/write of both artefacts)
- [ ] T005 [US1] Write a failing test for `etl.occupation_map.build_map` on a fixture cache (3 codes) that the JSON and Parquet match the schema, the chunk-set hash and the model identity; the UMAP step under `importorskip("umap")`
- [ ] T006 [US1] Implement `src/lonekrav/etl/occupation_map.py` and the `map` subcommand in `src/lonekrav/etl/cli.py` (lazy umap import with a clear error); run `uv run --group map lonekrav-etl map` on the real cache and commit the artefacts
- [ ] T007 [US1] Add both tables to `data/processed/data-dict.yaml` and run `data-dict validate-data`
- [ ] T008 [US1] Write failing tests in `tests/unit/test_occupation_map.py` against the committed artefacts: SC-001 (stored neighbours equal neighbours recomputed from the Parquet pairs), SC-002 (2511 → 2512 and 2519 in the top three; 2221 → 2239 and 2224 in the top five), and no text field anywhere
- [ ] T009 [US1] Write failing tests in `tests/integration/test_map_api.py` and `tests/integration/test_mcp.py` for `/occupations/{code}/neighbours`, `/closeness` (404, 422, same description) and both MCP tools, each carrying `honest_fit`
- [ ] T010 [US1] Implement `Service.neighbours` and `Service.closeness`, the routes, the tools, and artefact loading with the stale check in `src/lonekrav/app.py`; regenerate the OpenAPI types

## Phase 3: User Story 2 — See the map (P2)

- [ ] T011 [US2] Load the `dataviz` skill and pick and validate 10 categorical colours for the major groups in both themes (`validate_palette.js`); add them as tokens in `frontend/src/index.css`
- [ ] T012 [US2] Write failing tests in `frontend/src/lib/mapScale.test.ts` for the viewBox zoom and pan and the nearest-point lookup (stacked points return every code at that spot)
- [ ] T013 [US2] Implement `frontend/src/lib/mapScale.ts`
- [ ] T014 [US2] Add `GET /api/v1/map` (test first in `test_map_api.py`) and record it as a page fixture
- [ ] T015 [US2] Write failing tests in `frontend/src/components/OccupationMap.test.tsx`: 429 points; colour per group; group labels once; a tooltip with titles, the median and the stacked list; keyboard focus through the focus set; the table view; the caption
- [ ] T016 [US2] Implement `frontend/src/components/OccupationMap.tsx`

## Phase 4: User Story 3 — The map in search (P2)

- [ ] T017 [US3] Write failing tests in `frontend/src/views/SearchView.test.tsx`: hits outlined, selected codes filled with 5 lines, the layout unchanged across searches, `<details>` on narrow screens; and in `NumberView.test.tsx`: "Similar work" lists 5 neighbours by similarity, and the pair sentence appears with exactly two codes
- [ ] T018 [US3] Wire the map into `SearchView.tsx` and "Similar work" into `NumberView.tsx`
- [ ] T019 [US3] Update `frontend/e2e/views.spec.ts` (a map screenshot at both widths; axe; no sideways scroll); measure SC-004 with a 4× CPU throttle

## Phase 5: Polish

- [ ] T020 Build the container with `LONEKRAV_PORT=8001`; confirm `import umap` fails inside it, measure the image size difference (SC-006) and memory with `scripts/container_memory.py`
- [ ] T021 Write `references/occupation-map.md` (curl output, screenshots, SC-003 and SC-004 figures); update `README.md` and `CLAUDE.md` ("Things worked out in Feature 007")
- [ ] T022 Full gates, then the PR with evidence
