# Quickstart: validating Feature 002

Prerequisites: Feature 001 built locally (`data/processed/`, `data/lonekrav_milvus.db` with both
models). No `OPENROUTER_KEY` needed.

## 1. Tests

```bash
uv run pytest                       # default suite: offline, no models
uv run pytest -m benchmark          # the gate: must be all green before merge (FR-020)
```

Expected: the default suite passes. The benchmark prints fast and full modes, n beside every
metric, the 001 numbers beside the new ones, and the diagnosis table.

## 2. Diagnosis and benchmark by hand

```bash
uv run lonekrav-etl build           # regenerates benchmark_generated.json with the stricter leak check
uv run lonekrav-etl index           # the hold-out set changed, so the index is rebuilt (embeddings cached)
uv run lonekrav-etl benchmark       # writes data/processed/benchmark_results.json
```

Check: full mode English–Swedish gap ≤ 5 points, Recall@5 ≥ 0.80 per language in both modes,
fused ≥ each method, hand-written overlap ≥ 0.80. Paired n is printed; if it is below 60, stop and
raise it (research R1).

## 3. Serve and exercise every operation (SC-008)

```bash
uv run lonekrav-serve &
uv run python scripts/api_smoke.py > references/api-smoke.md   # every route once, requests + responses
```

The smoke script uses only made-up offers and public example text (FR-033). Spot checks inside it:

| Call | Expect |
|---|---|
| eligibility 2512, 40 000, first permit, filed 2026-06-16 | pass, 34 470, margin 5 530 |
| same, filed 2026-06-15 | threshold 33 390 |
| 3511, first permit, filed 2026-10-21 | 28 725 (exempt) |
| 5343 | not_permitted |
| 9210 | 75 %, partial-ban warning |
| extension 3511, filed 2026-11-30, granted 2026-01-10 | 80 %, 30 640 |
| extension, filed 2026-12-02, granted 2026-01-10 | 90 % |
| 40 000 at 80 % FTE | threshold unchanged, part-time warning |
| search "backend developer" fast and full | 2512 in top 5; full has three scores |
| search "Aktuarie/Försäkringsaktuarie/Försäkringsmatematiker" | `title_list` has 3 parts; 2121 in top 5 |
| search "asdf" | `low_confidence: true` |
| parse-job-ad on a sample ad | title kept; company and benefits not kept |
| salary 2512, age band 25-34 | 2025 median 53 500, TAB5932; simulated block flagged |
| compare 2512, 2511, 3512 with an offer | three columns in that order, each with eligibility |
| compare one code | 422 naming the 2–5 range |
| legal/timeline | medians 2021–2026, rules with sources |

## 4. Latency (SC-003)

```bash
uv run python scripts/latency.py    # 200 fast queries, 50 full queries incl. 600-word ads, against the running server
```

Expected: fast p95 < 50 ms, full p95 < 1 s. Record the output in the PR.

## 5. Registry check

Compare `GET /api/v1/legal/timeline` with the two Migrationsverket pages cited in research R6, and
record the date checked in `legal_constants.yaml` (`checked_on`).
