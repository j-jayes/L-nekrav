# Quickstart: validate Your number

## Prerequisites

The 004/005 setup (index built, `frontend/` installed). No network is needed.

## Tests

```bash
rtk proxy uv run pytest -q
uv run python scripts/export_openapi.py && (cd frontend && npm run gen)   # after model changes
(cd frontend && npm test && npm run build)
```

## By hand

```bash
PORT=8010 uv run lonekrav-serve &
curl -s '127.0.0.1:8010/api/v1/occupations/2511/salary?age_band=25-34&region=SE11' | jq '.simulated | {p25, p75, applied, left_out, formula}'
curl -s '127.0.0.1:8010/api/v1/occupations/2511/salary?region=SE99' -o /dev/null -w '%{http_code}\n'   # 422
curl -s -X POST 127.0.0.1:8010/api/v1/eligibility -H 'content-type: application/json' \
  -d '{"code":"2511","monthly_salary_sek":60000,"fte_percent":100,"application_type":"first_permit","filed_on":"2026-10-27","decided_on":"2026-10-27"}' | jq '.status, .market_position'
curl -s '127.0.0.1:8010/api/v1/occupations/2511/salary' | jq '.thresholds[0].source'
```

Expected:
- the estimate is about 44 700–62 500 with both factors applied;
- 60 000 sits between the median (56 200) and P75 (66 700);
- every threshold line has a source.

## Page

```bash
(cd frontend && BASE_URL=http://127.0.0.1:8010 npx playwright test e2e/views.spec.ts)
```

Then run the candidate walk from the scratchpad for `/?view=number&codes=2511,2512,2519&age=25-34&region=SE11`
with 60 000 typed, at 390×844 and 1280×800:
- SC-001: the first card's position, estimate and floor check are visible without scrolling on the
  phone.
- SC-004: the page height on desktop is at most half of the 005 compare view's (about 2 200 px).

Record the screenshots and heights in `references/your-number.md`.
