# Occupation map (Feature 007): evidence

Recorded 2026-10-27 on branch 007-occupation-map, against `PORT=8010 uv run lonekrav-serve`.
Every block is command output.

## Building the map

```text
$ uv run --group map lonekrav-etl map
occupation map: 429 codes from data/raw/embeddings/harrier-6f0c7287a1e1.npz, UMAP {'n_neighbors': 15, 'min_dist': 0.1, 'metric': 'cosine', 'random_state': 0, 'umap_version': '0.5.12'}

$ ls -l data/processed/occupation_map.json data/processed/occupation_similarity.parquet
290640 data/processed/occupation_map.json
311950 data/processed/occupation_similarity.parquet

$ uv run --group map python references/occupation_map_probe.py data/raw/embeddings/harrier-6f0c7287a1e1.npz
pairwise cosine p5/p50/p95/max 0.645 0.736 0.843 1.0
2511 [('2512', 0.939), ('2519', 0.935), ('1312', 0.921), ('1311', 0.921), ('2514', 0.907)]
2221 [('2239', 0.921), ('5323', 0.905), ('5330', 0.9), ('2224', 0.895), ('5349', 0.886)]
2-D top10 within full top20 = 0.6466200466200466
```

## Serving

```text
$ curl -s '127.0.0.1:8010/api/v1/occupations/2511/neighbours?k=5' | jq -c '.neighbours[] | {code, cosine, percentile, same_description, median_sek}'
{"code":"2512","cosine":0.939,"percentile":99,"same_description":false,"median_sek":53500}
{"code":"2519","cosine":0.935,"percentile":99,"same_description":false,"median_sek":55600}
{"code":"1312","cosine":0.921,"percentile":99,"same_description":false,"median_sek":71700}
{"code":"1311","cosine":0.921,"percentile":99,"same_description":false,"median_sek":75400}
{"code":"2514","cosine":0.907,"percentile":99,"same_description":false,"median_sek":49000}

$ curl -s '127.0.0.1:8010/api/v1/closeness?a=2511&b=2512' | jq -c '{cosine, percentile, same_description}'
{"cosine":0.939,"percentile":99,"same_description":false}
$ curl -s '127.0.0.1:8010/api/v1/closeness?a=1311&b=1312' | jq -c '{cosine, percentile, same_description}'
{"cosine":0.998,"percentile":null,"same_description":true}
$ curl -s -o /dev/null -w '%{size_download} bytes in %{time_total} s
' 127.0.0.1:8010/api/v1/map
233077 bytes in 0.060019 s
```

## The page

Screenshots: `references/web-client-screenshots/search-{desktop,phone}.png` (written by
`frontend/e2e/views.spec.ts`, with the map open and 2512 and 3511 selected).

| Check | Measured | Target |
|---|---|---|
| SC-001: stored neighbours equal those recomputed from the pair table | all 429 codes (`test_stored_neighbours_are_the_ten_most_similar_by_the_pair_table`) | all |
| SC-002: 2511 → 2512, 2519 in the top three; 2221 → 2239, 2224 in the top five | yes (output above) | yes |
| SC-003: share of each code's 10 nearest on the map among its 20 nearest in full dimension | 0.647 | ≥ 0.5 |
| SC-004: frames while the pointer moves over the map, phone viewport, 4× CPU throttle | median 16.7 ms, p95 16.7 ms, max 33.2 ms (one dropped frame of 117) | each under 16 ms: **nearly met**, since rAF intervals are vsync-bound at 16.7 ms |
| SC-005: axe serious/critical, sideways scroll | 0 and none, at both widths | 0 and none |

## Design changes made while building

- **No colour by major group.** The spec said to colour points by SSYK major group. The dataviz
  skill's all-pairs check allows at most three categorical hues on a scatter, and the major groups
  are skill levels (1 managers, 2 advanced higher education, 3 higher education, …), which UMAP's
  domain clusters cut across. IT alone spans 1311, 2511 and 3511, so group labels at group
  medians landed in meaningless places. Points are therefore neutral grey. Colour marks only the
  codes in play (search results, selected codes, their five nearest), and a code's group is read
  in the readout and the table.
- **"Same official description" is semantic, not geometric.** UMAP draws 1311 and 1312 about
  0.008 apart (a few pixels), so the readout lists a code together with its neighbours at cosine
  ≥ 0.99, not with whatever shares its pixel.
- **The map shows its own limits.** 2511's two nearest codes by cosine after 2512 and 2519 are the
  IT-manager codes 1311 and 1312, and UMAP draws them some way off. The caption says that map
  distances are approximate and the similarity figures are exact.
- `/api/v1/map` is about 230 KB uncompressed. The page loads it once per visit.

## The container (T020)

| Check | Measured |
|---|---|
| `umap` and `numba` inside the image | `importlib.util.find_spec` returns None for both |
| Image size | 3 846 459 188 bytes against 3 845 761 322 for the 005 image: +698 KB (SC-006: under 1 MB) |
| Memory, `scripts/container_memory.py` on a fresh container | peak 4.31 GiB of 5.00 GiB, anon 4.19 GiB, swap 0, OOM 0 (004/005: peak 4.40 GiB, anon 4.13 GiB) |
| Smoke | `/api/v1/occupations/2511/neighbours?k=3` gives 2512, 2519, 1312; `/api/v1/map` is 200 (233 077 bytes) |
