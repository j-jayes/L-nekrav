# Quickstart: validate Feature 001 end to end

Prerequisites: uv, network access for the first fetch, about 3 GB free disk for the model caches.
No `OPENROUTER_KEY` is needed.

```bash
uv sync
uv run pytest                              # offline, fake embedder, < 30 s
uv run lonekrav-etl fetch                  # raw files to data/raw/ with .meta.json
uv run lonekrav-etl build                  # processed files to data/processed/
uv run lonekrav-etl measure-models         # writes references/embedding-benchmark.md
uv run lonekrav-etl index                  # data/lonekrav_milvus.db
uv run lonekrav-etl benchmark              # table + data/processed/benchmark_results.json
uv run pytest -m benchmark                 # asserts SC-004, SC-005, SC-006
```

## Checks and expected outcomes

| # | Check | Expected |
|---|---|---|
| 1 | Profile count in `ssyk_profiles.json` | 429, every one with `title_sv`, `title_en` and a Swedish description (SC-001) |
| 2 | Profile 2512 | ISCO codes 2511, 2512, 2513, 2514 and 2521; at least 20 Swedish synonyms; no legal flags |
| 3 | Profiles 3511, 5343 and 9210 | `exempt_75`; `banned`; `exempt_75` plus `partially_banned` |
| 4 | `discrepancies.csv` | 0110, 0210 and 0310 missing from the structure file; 54 codes not in JobTech, with the 50 manager codes showing their merged `jobtech_code` |
| 5 | Salary 0000 in 2025 | median 38 300 |
| 6 | Salary 2512 in 2025 | mean 55 500, median 53 500, P10 39 600, P25 46 200, P75 62 600, P90 72 600, from TAB5932 |
| 7 | Age 2512 in 2025, 18–24 | mean 36 100, headcount null and listed in `suppressed` |
| 8 | Years present | 2014 to 2025; 2014–2022 rows from TAB4265 and TAB4264 with null CIs |
| 9 | Ten-code spot check against statistikdatabasen.scb.se | exact match (SC-002) |
| 10 | Re-run `build` | `git diff --stat data/processed` shows no changes |
| 11 | Delete `data/lonekrav_milvus.db`, run `index` with models and the ILO file cached and the network off | it rebuilds |
| 12 | Size of `data/lonekrav_milvus.db` | under 200 MB (SC-008) |
| 13 | Spot queries through `core.search` | "backend developer" → 2512 in the top 5; "sjuksköterska" → a 222x code in the top 5; "management consultant" → 2421 in the top 5 |
| 14 | `benchmark_results.json` | fused Recall@5 ≥ 0.80 in both languages; EN−SV gap ≤ 5 points; fused ≥ each single method |
| 15 | Fetch failure (covered by the mock-transport test in T007) | exit 1, message names the source and the URL, cached files unchanged |

Spot query one-liner:

```bash
uv run python -c "from lonekrav.core.search import search; [print(h.fused_rank, h.code, h.title_en, h.scores) for h in search('backend developer')]"
```
