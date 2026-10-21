# Contract: web API version 1

Served by `lonekrav-serve` (default `http://127.0.0.1:8000`). JSON in and out; body and field
shapes are the core models in [data-model.md](../data-model.md). The machine-readable contract is
the generated OpenAPI document at `GET /api/v1/openapi.json` (FR-029); this file is the
human-readable index of it.

| Method and path | Request | Response | Story |
|---|---|---|---|
| `POST /api/v1/eligibility` | `EligibilityRequest` | `EligibilityAnswer` | 1 |
| `POST /api/v1/search` | `SearchRequest` | `SearchAnswer` | 2, 4 |
| `POST /api/v1/parse-job-ad` | `{"text": str}` | `ParsedAd` | 4 |
| `GET /api/v1/occupations/{code}` | — | `OccupationProfile` (ILO text omitted) | 6 |
| `GET /api/v1/occupations/{code}/salary?age_band=25-34&on=2026-10-21` | query | `SalaryPayload` | 5 |
| `POST /api/v1/compare` | `CompareRequest` | `Comparison` | 6 |
| `GET /api/v1/legal/timeline` | — | `list[TimelineEvent]` | 7 |
| `GET /api/v1/benchmark` | — | latest benchmark results file | 3 |
| `GET /api/v1/health` | — | `{"status": "ok", "models_loaded": [...], "index_chunks": int}` | — |

Rules:

- **Errors**: 422 for invalid input, with FastAPI's standard body naming the field (`loc`) and the
  rule (`msg`); 404 for an unknown code, naming it; 500 with `{"detail": "internal error"}` and no
  path or traceback. Search text longer than 20 000 characters and `k` > 20 are 422s.
- **Honest fit**: `SearchAnswer`, `Comparison` and `EligibilityAnswer` always carry their
  honest-fit or disclaimer text. No endpoint takes a sort parameter, and none orders codes by
  threshold.
- **Fallback**: `mode: "full"` when Harrier cannot load returns 200 with `mode_used: "fast"` and a
  `fallback_reason`.
- **Dates**: ISO 8601 (`2026-06-16`). Money: whole SEK as integers. Percentages: decimals
  (`90`, not `0.9`).
- **No key needed**: no endpoint reads `OPENROUTER_KEY` (FR-032).
- **No content logging**: request bodies are not written to logs (R7).

## Examples

```http
POST /api/v1/eligibility
{"code": "2512", "monthly_salary_sek": 40000, "fte_percent": 100,
 "application_type": "first_permit", "filed_on": "2026-06-16"}
```
→ `status: "pass"`, `rule_id: "salary_90"`, `threshold_sek: 34470`, `margin_sek: 5530`,
`median.amount: 38300`.

```http
POST /api/v1/search
{"text": "backend developer", "mode": "fast"}
```
→ `mode_used: "fast"`, `hits[0..4]` containing code `2512`, `honest_fit` present.

## Core functions behind the routes (reused by 003)

```text
core.eligibility.evaluate(req: EligibilityRequest, registry=None) -> EligibilityAnswer
core.search.run(req: SearchRequest, engine: SearchEngine) -> SearchAnswer
core.adparse.parse(text: str, embedder) -> ParsedAd
core.salary.payload(code: str, on: date, age_band: str | None = None) -> SalaryPayload
core.compare.compare(req: CompareRequest) -> Comparison
core.legal.load_registry() -> Registry ; Registry.timeline() -> list[TimelineEvent]
```

`SearchEngine` holds the store, the loaded embedders and the in-memory dense matrices (R2); the app
builds one in its lifespan and tests build one over a fixture index with the FakeEmbedder.
