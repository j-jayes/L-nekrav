# Data model: Occupation map

## Artefact `data/processed/occupation_map.json`

```text
{
  "model": "microsoft/harrier-oss-v1-0.6b@f9b9dc8d…:1024:float32",
  "chunk_kinds": ["title", "desc_sv", "desc_en"],
  "ilo_excluded": true,
  "chunk_set_sha256": "…",
  "umap": {"n_neighbors": 15, "min_dist": 0.1, "metric": "cosine", "random_state": 0, "umap_version": "…"},
  "built_on": "2026-10-27",
  "pair_quantiles": [0.41, …, 1.0],      // 101 values, the 0th–100th percentile of all pair cosines
  "points": [
    {"code": "2511", "x": 0.4123, "y": 0.6610, "major_group": "2", "chunks": 14,
     "neighbours": [{"code": "2512", "cosine": 0.939}, … 10]}
  ]
}
```

- Points are sorted by code. Cosines are rounded to 3 decimals and positions to 4.
- The file holds no text other than codes and the model identity. Titles come from the profiles at
  serve time.

## Core models (`core/occupation_map.py`)

- **MapPoint**: code, x, y, major_group, chunks, neighbours: list[Neighbour].
- **Neighbour**: code, cosine.
- **OccupationMap**: the artefact's fields, plus `stale: bool`, which is set at load when the model
  identity differs from the index's.
- **NeighbourAnswer** (served): code, neighbours: list[{code, title_sv, title_en, cosine,
  median_sek: int | null, median_year: int | null}], honest_fit.
- **Closeness** (served): a, b, cosine, percentile (int | null; null when same_description),
  same_description, honest_fit.

## Artefact `data/processed/occupation_similarity.parquet`

Every unordered pair: `code_a < code_b` (str), `cosine` (float32). That is 91 806 rows, sorted, and
written with `statistics=False` like the salary files. Closeness for any pair reads from it; vectors
are never served. It is loaded into a dict keyed by pair at start.

## Data dictionary

Add the tables `occupation_map` and `occupation_similarity` to `data/processed/data-dict.yaml`. Record
its provenance (derived from the Harrier embeddings of SCB/JobTech/ESCO texts, ILO excluded), note
that it contains no text, and validate it.
