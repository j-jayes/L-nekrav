# Container smoke test

Run 2026-10-23T13:44:28 against `http://127.0.0.1:8001` by `scripts/container_smoke.py`.

Image `lonekrav:latest`: 3.85 GB.

| Check | Result |
|---|---|
| `GET /` (the page) | 200 text/html; charset=utf-8, title present: True |
| `GET /api/v1/health` | {"status":"ok","models_loaded":["kblab"],"index_chunks":9554} |
| Agent card | lonekrav-advisor at http://localhost:8000/a2a |
| MCP `tools/list` | compare_occupations, evaluate_permit_eligibility, extract_job_ad_signal, get_occupation_market, get_occupation_salary, search_occupations |
| Fast search (en1 ad) | fast: ['2512', '3513', '2519', '2511', '3512'] |
| Full search (en1 ad) | full: ['2512', '3513', '2519', '2511', '4119'] |
| Market for 2512 (Feature 005) | live available (1187 ads), regional 2025 (9 rows), history 2016–2025 |
| `.env` inside the container | 0 files |
| `OPENROUTER_KEY` in the container | not set |
| Both searches with no network (from inside) | [('fast', 'fast'), ('full', 'full')] |
| Market live count with no network (from inside) | unavailable connection error 0.1 s |
