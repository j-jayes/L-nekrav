# Data model: Your number

No new datasets or artefacts. All models live in core and are shared by REST, MCP and the page,
whose types are generated from the OpenAPI schema.

## MarketPosition (new, `core/salary.py`)

Where a full-time-equivalent monthly amount sits among one distribution's published percentiles.

| Field | Type | Notes |
|---|---|---|
| amount_sek | int | The full-time equivalent compared (salary ÷ share of full time) |
| year | int | The distribution's year |
| source_table | str | For example TAB5932 |
| lower | PercentileRef \| null | The nearest published percentile at or below; null means below every published one |
| upper | PercentileRef \| null | The nearest published percentile at or above; null means above every published one |
| at | PercentileRef \| null | Set when the amount equals a published percentile |
| missing | list[str] | Percentile names SCB does not publish that lie between `lower` and `upper` |
| no_data | bool | True when the distribution publishes no percentile at all |

`PercentileRef` is `{name: "p10" | "p25" | "median" | "p75" | "p90", value_sek: int}`.

Rules:
- There is no interpolation; values are copied from the distribution.
- The ordering is p10 < p25 < median < p75 < p90.

## SimulatedPercentiles (extended)

The existing fields are kept: `age_band`, `year`, p10…p90, `is_simulated: true`, `formula` and
`inputs`. Changes:

| Field | Change |
|---|---|
| age_band | Now `str \| null` (an estimate may be area-only) |
| region | **New**, `str \| null`: the national area code (SE11…SE33) |
| applied | **New**, `list["age" \| "region"]` |
| left_out | **New**, `list[{factor: "age" \| "region", reason: str}]` |
| formula | Built from `applied`, for example "percentile × (age-band mean ÷ all-ages mean) × (area mean ÷ Sweden mean); the two factors are assumed independent" |

Rules:
- When `applied` is empty, there is no estimate. The payload's `simulated` is then null, and
  `estimate_note` (below) gives the reasons.
- A null percentile in gives a null out.

## SalaryPayload (extended)

| Field | Change |
|---|---|
| simulated | Now set when `age_band` or `region` is given and at least one factor applies |
| estimate_note | **New**, `str \| null`: why no estimate was made, when one was requested |

## ThresholdLine (extended)

| Field | Change |
|---|---|
| source | **New**, `Source`: the rule's registry source, with URL, ref and checked-on date |

## EligibilityAnswer (extended)

| Field | Change |
|---|---|
| market_position | **New**, `MarketPosition \| null`: null for an unknown code or no distribution |

## Page state (frontend)

- **The address** holds `view` (`search` \| `number` \| `legal`, where `compare` parses as `number`),
  `codes`, `age` and `region`.
- **Memory only**: the number and the offer draft (`lib/offer.ts` `Draft`, defaults from
  `emptyDraft()`), the ad and the background.
- **Selection**: the `simulated` map and its action are removed.
