# Search latency

Two runs of `scripts/latency.py`, an hour apart, same code on the fast path. The laptop was
in normal use (browser, editor) both times; the spread between runs is part of the result.

## Run 1

Run 2026-10-21 22:21 on arm64 Darwin by `scripts/latency.py` (client-side round trips, models warm).

| Mode | n | median ms | p95 ms | max ms | budget ms | |
|---|---|---|---|---|---|---|
| fast (titles) | 200 | 31.6 | 40.2 | 84.2 | 50 | pass |
| full (all) | 50 | 522.5 | 1238.1 | 1742.8 | 1000 | FAIL |
| full: titles | 25 | 156.8 | 178.4 | 178.7 | 1000 | pass |
| full: ~600-word texts | 25 | 921.6 | 1674.9 | 1742.8 | 1000 | FAIL |

## Run 2 (adds pasted ads searched with `parse_ad`)

Run 2026-10-21 22:33 on arm64 Darwin by `scripts/latency.py` (client-side round trips, models warm).

| Mode | n | median ms | p95 ms | max ms | budget ms | |
|---|---|---|---|---|---|---|
| fast (titles) | 200 | 45.5 | 62.7 | 103.4 | 50 | FAIL |
| full (all) | 50 | 549.2 | 1048.3 | 1991.6 | 1000 | FAIL |
| full: titles | 25 | 182.2 | 211.2 | 215.8 | 1000 | pass |
| full: ~600-word texts | 25 | 929.8 | 1711.1 | 1991.6 | 1000 | FAIL |
| full + parse_ad: pasted ads | 50 | 314.3 | 384.7 | 633.7 | 1000 | pass |

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

## Where fast mode spends its time

Measured in-process (no HTTP) over the same 200 titles, models warm, 2026-10-21:

| Step | median ms | p95 ms |
|---|---|---|
| KBLab encode, 1 thread | 34.5 | 40.5 |
| Dense search, numpy, pool 50 | 0.4 | 0.5 |
| BM25, pool 50 | 6.2 | 9.6 |
| Reduce, fuse, titles, legal flags | 0.2 | 0.2 |
| Whole `run()` (three rounds) | 40–43 | 47–59 |

Fast mode meets the 50 ms budget on a quiet machine and misses it under load: query encoding alone
is 35–40 ms. A quantised or ONNX KBLab is the remaining lever (research R2 rejected it as not
needed; this measurement reopens it).

Full mode meets 1 s for titles and for pasted ads searched with `parse_ad` (p95 385 ms on the ten
made-up ads, which are about 100 words each). Raw 600-word texts searched without parsing miss it
(p95 1.7 s) because Harrier reads all ~800 tokens.
