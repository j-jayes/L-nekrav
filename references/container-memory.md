# Container memory

Run 2026-10-22T15:56:58 against `http://127.0.0.1:8001` by `scripts/container_memory.py`, on a freshly started container (Apple M2 Pro, Docker Desktop, linux/arm64). `docker stats` sampled every second.

**Peak 4.40 GiB of the 5.00 GiB limit (88 %).**

| Step | Status | Request time | Peak during step |
|---|---|---|---|
| idle after start-up | - | 0.00 s | 1.87 GiB |
| fast search, typed title | 200 | 1.13 s | 1.89 GiB |
| fast search, pasted ad | 200 | 0.65 s | 1.89 GiB |
| full search, pasted ad (loads Harrier) | 200 | 9.53 s | 4.40 GiB |
| full search again | 200 | 2.62 s | 4.40 GiB |
| eligibility | 200 | 0.05 s | 4.39 GiB |
| compare three codes | 200 | 0.44 s | 4.39 GiB |

The kernel's view at the end (cgroup v2): process (anon) memory 4.13 GiB, page cache 0.40 GiB, high-water mark 4.57 GiB, swap in use 0.0 MiB, OOM kills 0. The limit was reached 0 times; the page cache (model and index files) fills up to the limit and is trimmed there, so these events alone are harmless.

## Why the cap is 5 GB, not 4 GB

The constitution's budget was 4 GB (decided 2026-10-20, from 001's per-model measurements: KBLab
0.96 GB and Harrier 2.56 GB peak RSS, each in its own process). The container holds both models
plus the server, the search matrices and the MCP and A2A stacks, and needed more. The maintainer
raised the cap to 5 GB on 2026-10-22, after these measurements:

- **Under `mem_limit: 4g`** (an earlier build of the same code, before the uv cache was dropped
  from the image): `docker stats` held at 3.98 GiB of 4.00 GiB once Harrier had loaded. The cgroup
  showed 4.23 GB of process (anon) memory, only 39 MB of page cache, and 3 825 limit events.
  Process memory itself was at the cap, so Docker Desktop's swap absorbed the overflow. Every
  request still answered 200, and nothing was OOM-killed. The run is below.
- **With the cap lifted to 8 GB**: 4.20 GiB steady, and a cgroup high-water mark of 4.54 GiB.
- **Under `mem_limit: 5g`** (above): process memory is about 4.1 GiB, with no swap and no OOM.
  In one of three runs the page cache filled to the limit and was trimmed (906 limit events, 0.8 MB
  in swap, 131 anonymous refaults), which is harmless.

The run under the 4 GB cap:

**Peak 3.98 GiB of the 4.00 GiB limit (100 %).**

| Step | Status | Request time | Peak during step |
|---|---|---|---|
| idle after start-up | - | 0.01 s | 1.71 GiB |
| fast search, typed title | 200 | 1.72 s | 1.72 GiB |
| fast search, pasted ad | 200 | 0.89 s | 1.74 GiB |
| full search, pasted ad (loads Harrier) | 200 | 9.36 s | 3.98 GiB |
| full search again | 200 | 1.37 s | 3.98 GiB |
| eligibility | 200 | 0.20 s | 3.98 GiB |
| compare three codes | 200 | 0.21 s | 3.98 GiB |
