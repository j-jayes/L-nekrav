# HTTP contract changes: Your number

## `GET /api/v1/occupations/{code}/salary?age_band=&region=&on=`

- **New query parameter `region`**: one of `SE11 SE12 SE21 SE22 SE23 SE31 SE32 SE33`. Any other
  value gives a 422 with the allowed values, just as an unknown `age_band` does.
- **`simulated`**: set when `age_band` or `region` is given and at least one factor applies (see
  [data-model.md](../data-model.md)). Each factor not applied is listed in `simulated.left_out`.
- **`estimate_note`**: set when an estimate was requested but neither factor applies, or the
  distribution has no percentiles. In that case `simulated` is null.
- **`thresholds[].source`**: the rule's legal source `{key, ref, url, checked_on}`.

Example (2511, `age_band=25-34&region=SE11`, 2025): `simulated.p25` ≈ 44 711 and
`simulated.p75` ≈ 62 520, with `applied: ["age", "region"]`, `inputs` TAB5932 2025, TAB5844 2025
and TAB5696 2025, and `is_simulated: true`.

## `POST /api/v1/eligibility`

- **New field `market_position`** on the answer. It is computed from the code's latest distribution
  and the full-time equivalent of `monthly_salary_sek`. It is null for codes with no distribution.

Example (2511, 60 000 SEK at 100 %):

```json
{
  "amount_sek": 60000,
  "year": 2025,
  "source_table": "TAB5932",
  "lower": {"name": "median", "value_sek": 56200},
  "upper": {"name": "p75", "value_sek": 66700},
  "at": null,
  "missing": [],
  "no_data": false
}
```

## `POST /api/v1/compare`

- `codes` now accepts **1–5** distinct codes (was 2–5). The error message changes to match.
