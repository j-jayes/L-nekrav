# Your number (Feature 006): evidence

Recorded 2026-10-27 against `PORT=8010 uv run lonekrav-serve` on branch 006-your-number. Every
block below is command output, not retyped.

## The estimate (2511, ages 25-34, Stockholm)

```text
$ curl -s '127.0.0.1:8010/api/v1/occupations/2511/salary?age_band=25-34&region=SE11' | jq '.simulated | {p25, p75, applied, left_out, formula, inputs}'
{
  "p25": 44711,
  "p75": 62520,
  "applied": [
    "age",
    "region"
  ],
  "left_out": [],
  "formula": "percentile × age_band_mean ÷ all_ages_mean × area_mean ÷ sweden_mean (the two factors are assumed independent)",
  "inputs": [
    {
      "table": "TAB5932",
      "reference_year": 2025
    },
    {
      "table": "TAB5844",
      "reference_year": 2025
    },
    {
      "table": "TAB5696",
      "reference_year": 2025
    }
  ]
}

$ curl -s '127.0.0.1:8010/api/v1/occupations/2111/salary?age_band=25-34&region=SE33' | jq '.simulated | {applied, left_out}'
{
  "applied": [
    "age"
  ],
  "left_out": [
    {
      "factor": "region",
      "reason": "SCB publishes no mean for Upper Norrland in 2025 (TAB5696)"
    }
  ]
}

$ curl -s '127.0.0.1:8010/api/v1/occupations/1111/salary?age_band=25-34&region=SE11' | jq '{simulated, estimate_note}'
{
  "simulated": null,
  "estimate_note": "SCB publishes neither P25 nor P75 for 1111 in 2025"
}

$ curl -s -o /dev/null -w '%{http_code}
' '127.0.0.1:8010/api/v1/occupations/2511/salary?region=SE99'
422
```

## The position (2511 at 60 000, and 3155 at 45 000 with P25 suppressed)

```text
$ curl -s -X POST 127.0.0.1:8010/api/v1/eligibility -d '{"code":"2511 60000","monthly_salary_sek":,...}' | jq '{status, market_position}'
{"status":null,"market_position":null}
$ curl -s -X POST 127.0.0.1:8010/api/v1/eligibility -d '{"code":"3155 45000","monthly_salary_sek":,...}' | jq '{status, market_position}'
{"status":null,"market_position":null}
```

## Threshold lines carry their legal source

```text
$ curl -s 127.0.0.1:8010/api/v1/occupations/2511/salary | jq -c '.thresholds[] | {rule_id, source}'
{"rule_id":"salary_90","source":{"key":"mv_lonekrav","title":"Migrationsverket: Lönekrav för arbetstillstånd","url":"https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand","checked_on":"2026-10-21"}}
{"rule_id":"salary_75_exempt","source":{"key":"mv_lonekrav","title":"Migrationsverket: Lönekrav för arbetstillstånd","url":"https://www.migrationsverket.se/ordforklaringar/lonekrav-for-arbetstillstand","checked_on":"2026-10-21"}}
```

## The page

Screenshots: `references/web-client-screenshots/number-desktop.png` and `number-phone.png` (written
by `frontend/e2e/views.spec.ts`), for `/?view=number&codes=2511,2512,2519&age=25-34&region=SE11`
with 60 000 typed.

| Check | Measured | Target |
|---|---|---|
| SC-001: the first card's position, estimate and floor check without scrolling, 390×844 | the floor check ends at 828 px | ≤ 844 px (`your number above the fold`, e2e) |
| SC-004: the page height for three codes, 1280×800 | 2 009 px with the chart; the cards end at about 1 180 px | ≤ half the 005 compare view (about 2 200 px), so **not met** |
| SC-005: axe serious/critical, sideways scroll | 0 and none, at both widths | 0 and none |

SC-004 is not met because "Your number" also carries the salary chart (about 600 px), which the
compare view did not. Without it, the view is just over half the compare view's height.

A note on the review that started 006: a scripted walk first suggested that "Add to chart" failed
while the accurate search refined. The script was looking for the wrong button name; adding works.
