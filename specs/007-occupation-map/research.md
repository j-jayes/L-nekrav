# Research: Occupation map

All measurements were taken on 2026-10-27 from `data/raw/embeddings/harrier-6f0c7287a1e1.npz` and the
committed profiles. The scripts are scratchpad `pool.py` and `umap_try.py`, to be moved to
`references/occupation_map_probe.py` in T001.

## R1. One vector per code

- **Decision**: rebuild the chunks with `load_profiles` → `chunk_profile`, without `attach_ilo`, and
  keep the `title`, `desc_sv` and `desc_en` chunks with `ilo=False`. Look each one up in the Harrier
  cache by `sha256(text)`, the same key `encode_documents_cached` uses. Take the mean, then
  L2-normalise.
- **Measured**: 0 chunks missing from the cache. Chunks per code are 2 minimum, 10 median and 177
  maximum. Neighbours: 2511 → 2512 0.939, 2519 0.935, 1312, 1311, 2514; 2221 → 2239, 5323, 5330, 2224.
- **Why no `attach_ilo`**: profiles loaded from `data/processed/` carry no ILO text, because ILO text
  is never committed. Leaving out `attach_ilo` and also filtering `ilo=False` keeps out any ILO text
  that could arrive by another path. FR-001 excludes it, so the question of ILO-derived vectors never
  comes up.
- **Alternatives**:
  - Mean over every chunk: synonym lists are noisy, so they are left out.
  - KBLab: its English is weaker, and it is not the model the user chose.
  - Weighting by chunk length: there is no evidence it would help, so the plain mean is kept.

## R2. Closeness is the full-dimension cosine, explained as a percentile

- **Decision**: store each code's top 10 neighbours with their cosine. Also store 101 quantiles (the
  0th to 100th percentiles) of all 91 806 pair similarities. A pair's percentile is then the index
  of the last quantile below its similarity, accurate to a whole per cent (FR-003).
- **Measured**: pair similarity p5 0.645, p50 0.736, p95 0.843. 22 pairs score ≥ 0.99, mostly manager
  codes that differ only by level (1311/1312, 1321/1322 at 1.000).
- **Rule**: a pair at ≥ 0.99 reads "the same official description" (FR-009).

## R3. UMAP settings and determinism

- **Decision**: `umap-learn` with `n_neighbors=15`, `min_dist=0.1`, `metric="cosine"`,
  `random_state=0` and `n_jobs=1`. Positions are rescaled to [0, 1] and rounded to 4 decimals.
- **Measured**: on average 65 % of each code's 10 nearest in 2-D are among its 20 nearest in full
  dimension (SC-003 needs 50 %). nn=10/md=0.05 gave 67 % and nn=30/md=0.3 gave 58 %. The run takes
  6 s, and a rerun with the same seed gave identical positions.
- **Byte stability**: not guaranteed across platforms or numba versions. The artefact is therefore
  rebuilt only on purpose (`lonekrav-etl map`), never inside `build`, and the idempotence test of
  `build` does not cover it. Tests check structure and neighbours (exact numpy), not coordinates.

## R4. Dependency placement

- **Decision**: add a new uv dependency group, `map = ["umap-learn"]`. It is not in `default-groups`,
  so neither `uv sync` nor the container's `uv sync --no-dev` installs it. Run the build with
  `uv run --group map lonekrav-etl map`. The CLI imports umap lazily and fails with that command in
  the message if it is missing. The UMAP test uses `pytest.importorskip("umap")`.
- **Rationale**: the image stays unchanged except for a JSON file of about 60 KB (FR-006, SC-006).
  numba and llvmlite stay out of the serving path.

## R5. Serving and checking that the map matches the index

- **Decision**: `core/occupation_map.py` loads `data/processed/occupation_map.json` into
  `Service.map`. The artefact records the Harrier identity (`hf_id@revision:dim:dtype`) and a hash
  of the sorted chunk ids it used. At start, if the identity differs from `SPECS["harrier"]`, the
  server logs a warning and serves the map with `stale: true`. It does not refuse to start, because
  search must still work.
- **Alternative**: refusing to start was rejected because it would make a cosmetic feature able to
  take down the service.

## R6. Drawing 429 points

- **Decision**: hand-drawn SVG, like `SalaryChart`, with no chart library.
  - Hover uses a linear nearest-point scan (429 points is far below any cost that matters).
  - Zoom and pan are a `viewBox` transform driven by pointer events and +/−/reset buttons.
  - Major groups 0–9 take 10 categorical colours. Load the `dataviz` skill and validate them with
    `validate_palette.js` in both themes.
  - Points outside the focus set are drawn in `--color-grid` grey, so colour is meaningful only for
    the codes in play.
  - Group labels sit at each group's median position.
- **Rationale**: there is no new dependency, and the code matches the house style. d3-zoom was
  considered and is not needed for one transform.
