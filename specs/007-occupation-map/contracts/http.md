# HTTP contract: Occupation map

- **`GET /api/v1/map`**: the points, with `major_group` names (from SSYK's ten major groups, in
  English and Swedish), `pair_quantiles`, `model`, `umap`, `built_on` and `stale`. It has no titles,
  because the page already has them from search and the selection. About 60 KB.
- **`GET /api/v1/occupations/{code}/neighbours?k=10`**: a `NeighbourAnswer`, with k from 1 to 10.
  An unknown code gives 404.
- **`GET /api/v1/closeness?a=2511&b=2512`**: a `Closeness`. An unknown code gives 404, and a == b
  gives 422.

MCP:
- `get_similar_occupations(code, k=5)` returns a `NeighbourAnswer`.
- `get_occupation_closeness(a, b)` returns a `Closeness`.

Both descriptions say that similarity of descriptions never decides which code fits: the duties
do.
