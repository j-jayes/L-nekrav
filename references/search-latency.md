# Search latency

Run 2026-10-21 22:21 on arm64 Darwin by `scripts/latency.py` (client-side round trips, models warm).

| Mode | n | median ms | p95 ms | max ms | budget ms | |
|---|---|---|---|---|---|---|
| fast (titles) | 200 | 31.6 | 40.2 | 84.2 | 50 | pass |
| full (all) | 50 | 522.5 | 1238.1 | 1742.8 | 1000 | FAIL |
| full: titles | 25 | 156.8 | 178.4 | 178.7 | 1000 | pass |
| full: ~600-word texts | 25 | 921.6 | 1674.9 | 1742.8 | 1000 | FAIL |

## Where full mode spends its time on a 600-word text

Measured in-process (no HTTP) on 8 of the same texts, models warm, 2026-10-21:

| Step | median ms | max ms |
|---|---|---|
| KBLab encode, 1 thread (truncates at 384 tokens) | 124 | 139 |
| Harrier encode, default 6 threads (reads all ~800 tokens; limit 32 768) | 717 | 839 |
| Harrier encode, 1 thread | 1 138 | 1 265 |
| BM25 search, pool 200, 600-word query | 82 | 272 |
| Whole full-mode rank | 928 | 1 177 |

Harrier is most of the cost, and one thread makes it slower, so only KBLab uses one thread
(research R2). Research R3 expects a pasted ad to be parsed first, so that Harrier encodes only the
kept passages; SC-003 for long texts is re-measured with `parse_ad` once ad parsing exists (US4).
