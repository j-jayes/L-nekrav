# Container smoke test

Run 2026-10-22T15:57:14 against `http://127.0.0.1:8001` by `scripts/container_smoke.py`.

Image `lonekrav:latest`: 3.85 GB.

| Check | Result |
|---|---|
| `GET /` (the page) | 200 text/html; charset=utf-8, title present: True |
| `GET /api/v1/health` | {"status":"ok","models_loaded":["harrier","kblab"],"index_chunks":9554} |
| Agent card | lonekrav-advisor at http://localhost:8000/a2a |
| MCP `tools/list` | compare_occupations, evaluate_permit_eligibility, extract_job_ad_signal, get_occupation_salary, search_occupations |
| Fast search (en1 ad) | fast: ['2512', '3513', '2519', '2511', '3512'] |
| Full search (en1 ad) | full: ['2512', '3513', '2519', '2511', '4119'] |
| `.env` inside the container | 0 files |
| `OPENROUTER_KEY` in the container | '' (empty: not given) |
| Both searches with no network (from inside) | [('fast', 'fast'), ('full', 'full')] |

## Settings at run time

```text
$ OPENROUTER_KEY= LONEKRAV_PORT=8001 LONEKRAV_PUBLIC_URL=https://lonekrav.example.test docker compose up -d
$ curl -s 127.0.0.1:8001/.well-known/agent-card.json | jq -r ".supportedInterfaces[0].url"
https://lonekrav.example.test/a2a
$ # SendStreamingMessage with no key: states and text
"state": "TASK_STATE_SUBMITTED"
"state": "TASK_STATE_REJECTED"
"text": "Agent unavailable: no model key is configured (set OPENROUTER_KEY in .env)."
```

Build: 166 s for `docker compose build` after a Dockerfile change that re-ran the Python and
model layers (the node stage and base images were cached). Start-up to a healthy
`/api/v1/health`: 36 s.
