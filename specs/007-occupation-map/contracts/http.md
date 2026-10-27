# HTTP contract: Occupation map

- **`GET /api/v1/map`**: the points, each with its titles, its latest SCB median and year, and
  its legal flag kinds, all added at serve time (the artefact holds none of them). Also
  `major_groups` (SCB's names in Swedish and English), `pair_quantiles`, `model`, `umap`,
  `built_on` and `stale`. About 230 KB.
- **`GET /api/v1/occupations/{code}/neighbours?k=10`**: a `NeighbourAnswer`, with k from 1 to 10.
  Each neighbour carries its `percentile` and `same_description`, as `/closeness` would.
  An unknown code gives 404.
- **`GET /api/v1/closeness?a=2511&b=2512`**: a `Closeness`. An unknown code gives 404, and a == b
  gives 422.

MCP:
- `get_similar_occupations(code, k=5)` returns a `NeighbourAnswer`.
- `get_occupation_closeness(a, b)` returns a `Closeness`.

Both descriptions say that similarity of descriptions never decides which code fits: the duties
do.
