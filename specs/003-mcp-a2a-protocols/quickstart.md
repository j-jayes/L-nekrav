# Quickstart: validate Feature 003

You need the local index (from 001) and `uv sync`. `OPENROUTER_KEY` in `.env` is needed only for
steps 4 and 5.

## 1. Offline suite

```bash
rtk proxy uv run pytest -q          # the default suite, including MCP and A2A with a fake model
uv run pytest -m benchmark -q       # 9 passed (stop lonekrav-serve first: Milvus Lite lock)
```

## 2. Without a key

```bash
env -u OPENROUTER_KEY uv run lonekrav-serve   # if .env defines the key, move .env aside for this run
curl -s localhost:8000/api/v1/health
curl -s localhost:8000/.well-known/agent-card.json | jq .name        # "lonekrav-advisor"
uv run python scripts/a2a_stream.py --ad "Backend developer, Python APIs"
```

Expected result: the health check and the card answer, and the stream ends with
`TASK_STATE_REJECTED` and the "Agent unavailable" text in under 1 s.

## 3. MCP from Claude Code (evidence: `references/mcp-claude-code.md`)

```bash
uv run lonekrav-serve &
claude mcp add --transport http lonekrav http://localhost:8000/mcp
claude -p "Use the lonekrav tools: which SSYK codes fit 'backend developer building Python APIs', \
and what is the salary picture for the top code?" \
  --allowedTools "mcp__lonekrav__search_occupations,mcp__lonekrav__get_occupation_salary"
```

Expected result: Claude Code lists the five tools (`claude mcp list` shows `lonekrav` as connected).
The answer quotes the tool results, including the honest-fit text and the SCB table and year.

## 4. A2A streamed run (evidence: `references/a2a-stream.md`)

```bash
uv run lonekrav-serve &        # with OPENROUTER_KEY in .env
uv run python scripts/a2a_stream.py --ad-file <ad.txt> --background "..." \
  --offer '{"monthly_salary_sek": 52000, "fte_percent": 100, "application_type": "first_permit", "filed_on": "2026-10-01"}'
```

Expected result: the events print in the order given in [contracts/a2a.md](contracts/a2a.md): a
working status, then for each tool a progress status and a `ui_sync` artifact, then the memo, then
`TASK_STATE_COMPLETED`. The script prints the total time and the time spent in the model.

## 5. Live test

```bash
uv run pytest -m live -q        # skipped without OPENROUTER_KEY
```

## 6. REST unchanged

```bash
uv run python scripts/api_smoke.py > /tmp/smoke.md && diff <(grep -v fetched_at references/api-smoke.md) <(grep -v fetched_at /tmp/smoke.md)
```

Expected result: no difference apart from timestamps.
