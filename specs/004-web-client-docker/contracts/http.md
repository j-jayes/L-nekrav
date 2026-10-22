# Contract: HTTP changes in 004

The REST routes from 002, `/mcp` and `/a2a` from 003 are unchanged. Feature 004 adds the
following.

## `GET /` and `GET /assets/{file}` (R2)

| Condition | `GET /` | `GET /assets/x.js` |
|---|---|---|
| `frontend/dist/index.html` exists | 200 `text/html`, the built `index.html` (with any query string) | 200 with the file, 404 for an unknown file |
| no build | 404 `{"detail": "frontend not built: run npm ci && npm run build in frontend/"}` | 404 |

`/mcp`, `/a2a`, `/.well-known/agent-card.json` and `/api/v1/*` answer the same with or without a
build. The routes are registered before the MCP root mount.

## `GET /api/v1/legal/registry` (R9)

200 with the `Registry` model as JSON: `medians[]`, `median_publication_window`, `rules{}`,
`code_lists{}` (each with `codes: {code: title}`), `exemptions{}` and `statements{}`. Every row
carries `source {key, title, url, checked_on}`. It is the same object that `load_registry()` returns,
and it needs no parameters. `percent` is serialised as pydantic serialises `Decimal`.

## Agent card (R3)

`/.well-known/agent-card.json` → `supportedInterfaces[0].url` is `{LONEKRAV_PUBLIC_URL}/a2a`, with
the default `http://localhost:8000/a2a`. Nothing else in the card changes.

## Process settings

`lonekrav-serve` binds `HOST:PORT`, defaulting to `127.0.0.1:8000`.

## OpenAPI

`/api/v1/openapi.json` is committed as `frontend/src/api/openapi.json`. A pytest fails when they
differ. Regenerate it with `uv run python scripts/export_openapi.py`, then run `npm run gen` in
`frontend/`.
