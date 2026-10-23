# Quickstart: validate Feature 004

You need the local index and processed data from 001 (`uv run lonekrav-etl ...`), `uv sync`, Node
22 and Docker Desktop running. `OPENROUTER_KEY` in `.env` is needed only for step 5.

## 1. Offline suites

```bash
rtk proxy uv run pytest -q                 # includes static serving, card URL, /legal/registry, OpenAPI drift
cd frontend && npm ci && npm test          # Vitest: SSE parser, URL state, search session, selection, chart, views
npm run build                              # tsc --noEmit then vite build -> frontend/dist
```

## 2. The page from the local server

```bash
uv run lonekrav-serve &                    # serves frontend/dist at /
open "http://localhost:8000/?view=search&codes=2512,2514"
cd frontend && npx playwright test e2e/views.spec.ts   # screenshots at 390 and 1280 px, axe, no sideways scroll
```

Expected result:
- the screenshots are in `references/web-client-screenshots/`;
- axe reports no serious or critical violations;
- the selection survives a reload.

## 3. English and Swedish ad (SC-003)

```bash
npx playwright test e2e/ad-languages.spec.ts           # paste EN, read top 3; paste SV, read top 3
```

Expected result: the two sets of top three codes are the same. The ad's source link and the codes
are written to `references/web-client-e2e.md`.

## 4. The drawer with a fake advisor

```bash
uv run python scripts/serve_fake_advisor.py &          # same app with a scripted model: salary 2512, compare 2512,2511
npx playwright test e2e/advisor.spec.ts
```

Expected result:
- the progress lines appear in order;
- 2512 and 2511 are selected on the chart before the memo arrives;
- the memo shows its footer.

## 5. Live advisor run (needs the key)

The server is running with `OPENROUTER_KEY`. Open the drawer, paste the ad from step 3 and send
it. Record the timings and a screenshot in `references/web-client-e2e.md` (SC-008).

## 6. Container

```bash
docker compose up --build                  # one service, port 8000 (LONEKRAV_PORT), mem_limit 5g
uv run python scripts/container_memory.py  # fast, full (loads the accurate model), eligibility, compare
curl -s localhost:8000/.well-known/agent-card.json | jq '.supportedInterfaces[0].url'
LONEKRAV_PUBLIC_URL=https://example.test docker compose up -d && curl -s localhost:8000/.well-known/agent-card.json | jq '.supportedInterfaces[0].url'
OPENROUTER_KEY= docker compose up -d       # the advisor reports unavailable; the rest works
```

Expected result:
- the peak is under the 5 GB cap and is recorded in `references/container-memory.md`; if it is not, stop
  and report;
- the card's URL follows `LONEKRAV_PUBLIC_URL`;
- the Playwright views suite also passes against the container
  (`BASE_URL=http://localhost:8000 npx playwright test e2e/views.spec.ts`).
