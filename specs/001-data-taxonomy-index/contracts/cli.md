# Contract: `lonekrav-etl` command line

Entry point `lonekrav-etl = "lonekrav.etl.cli:main"` (argparse). Exit code 0 on success, 1 on a
failed step with a one-line cause on stderr naming the source and URL. No step prompts.

| Command | Reads | Writes | Network | Models |
|---|---|---|---|---|
| `fetch [--only SOURCE ...] [--force]` | — | `data/raw/<source>/...` plus `<file>.meta.json` (`url`, `fetched_at`, `sha256`) | yes | no |
| `build` | `data/raw/` | `data/processed/ssyk_profiles.json`, `salary_distributions.parquet`, `salary_age.parquet`, `discrepancies.csv`, `benchmark_holdout.json`, `benchmark_generated.json` | no | no |
| `index [--models kblab,harrier] [--db PATH]` | `data/processed/` | `data/lonekrav_milvus.db` (gitignored) | model download only | yes |
| `benchmark [--db PATH]` | index, `tests/eval/queries_handwritten.yaml`, `benchmark_generated.json` | `data/processed/benchmark_results.json`, a table on stdout | no | yes |
| `measure-models` | — | `references/embedding-benchmark.md` | model download only | yes |

Sources for `--only`: `scb_files`, `scb_pxweb`, `jobtech`, `ilo`, `esco`, `mis2012`.

Rules:

- `fetch` writes to a temporary file and renames it only when the download succeeds and parses, so a
  failure never replaces good cached data. Without `--force`, an existing cached file is kept.
- `build` and `index` are pure functions of their inputs. Running twice gives identical files.
- `MILVUS_URI` overrides `--db`.

# Contract: core Python API used by later features

```text
core.profiles.load_profiles(path=DEFAULT) -> dict[str, OccupationProfile]
core.salary.load_distributions(path=DEFAULT) -> list[SalaryDistribution]
core.salary.load_age_bands(path=DEFAULT) -> list[AgeBandSalary]
core.embeddings.get_embedder(name: "kblab" | "harrier") -> Embedder
core.search.search(query: str, *, methods=("kblab","harrier","bm25"), k=5, store=None) -> list[SearchHit]
```

`search` with `methods=("kblab","bm25")` is the fast path that Feature 002 will use while the user
is typing.
