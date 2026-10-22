# Server memory (Feature 002, task T057)

Resident memory (RSS) of the `lonekrav-serve` process, measured with `ps -o rss` on Apple M2 Pro,
2026-10-21, against the full index (9 551 chunks):

| Point | RSS |
|---|---|
| After start-up: KBLab, profiles, salary tables, Milvus Lite, dense matrices for both models | 1.64 GB |
| After the smoke transcript, which includes full-mode searches (Harrier loaded lazily) | 2.57 GB |
| After three more full-mode searches on a pasted ad | 2.60 GB |

This is resident memory after the requests, not a peak; per-model peaks are in
`embedding-benchmark.md`. Both are within the 4 GB container budget (plan, constraint). The
Milvus Lite server runs as a child process and is not included; Feature 004 measures the whole
container with `docker stats`.
