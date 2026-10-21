# Data model: Feature 002

All models are pydantic v2 and live in `src/lonekrav/core/` (Principle I). The API, and later MCP,
A2A and the web client, reuse them unchanged. Models from 001 (`OccupationProfile`,
`SalaryDistribution`, `AgeBandSalary`, `LegalFlag`, `SearchHit`) are reused; changes are marked.

## Legal registry (`core/legal.py`, data in `core/legal_constants.yaml`)

**Source**: `url`, `title`, `checked_on: date`.

**MedianRecord**: `amount: int` (SEK), `scb_reference_year: int`, `effective_from: date`,
`effective_to: date | None`, `source`.
- Periods do not overlap and leave no gaps; `effective_to` of one row is the day before the next
  row's `effective_from`.

**Rule**: `id` (`flat_13000`, `maintenance_80`, `salary_90`, `salary_75_exempt`,
`transition_maintenance_80`), `kind: "flat" | "share_of_median"`, `percent: Decimal | None`,
`amount: int | None`, `effective_from`, `effective_to | None`, `applies_to` (plain-language
condition), `source`.

**CodeList**: `kind: "exempt_75" | "banned" | "partially_banned"`, `codes: dict[code, note]`,
`effective_from`, `effective_to | None`, `source`.

**PersonalExemption**: `id` (`former_student_researcher`, `temporary_protection`,
`healthcare_licensing`, `young_tech_company`), `label`, `conditions: str`, `source`.

**Registry**: all of the above; `median_on(date) -> MedianRecord`, `rule(id)`,
`codes_on(kind, date)`, `timeline() -> list[TimelineEvent]`.
Validation on load: every row has a source and `checked_on`; medians are contiguous; amounts for
every median × percent reproduce the published table (R6).

**TimelineEvent**: `date`, `kind: "median" | "rule" | "code_list"`, `summary`, `source`.

## Eligibility (`core/eligibility.py`)

**EligibilityRequest**
| Field | Type | Rule |
|---|---|---|
| `code` | `str` | 4 digits, a known profile |
| `monthly_salary_sek` | `int` | > 0 |
| `fte_percent` | `int` | 1–100 |
| `application_type` | `"first_permit" \| "extension"` | |
| `filed_on` | `date` | |
| `decided_on` | `date \| None` | default today; ≥ `filed_on` |
| `current_permit_granted_on` | `date \| None` | required for extensions, forbidden otherwise |
| `exemptions` | `list[PersonalExemption id]` | unique; `former_student_researcher` only on first permits |

**EligibilityAnswer**
| Field | Type |
|---|---|
| `status` | `"pass" \| "fail" \| "not_permitted" \| "out_of_scope"` |
| `rule_id` | `str \| None` |
| `reason` | `str` (why this rule applies) |
| `percent` | `Decimal \| None` |
| `median` | `MedianRecord \| None` |
| `threshold_sek` | `int \| None` |
| `margin_sek`, `margin_percent` | `int \| None`, `float \| None` |
| `warnings` | `list[Warning]` |
| `sources` | `list[Source]` |
| `disclaimer` | `str` (collective agreements not checked; information, not legal advice) |

**Warning**: `kind: "part_time" | "stale_median" | "partial_ban"`, `message`, `source | None`.

Rule selection, in order:
1. Code banned on `decided_on` → `not_permitted`.
2. First permit decided before 2026-06-01, or extension filed before 2026-06-01 → `out_of_scope`.
3. Extension filed 2026-06-01 … 2026-12-01 with current permit granted before 2026-06-01 →
   `transition_maintenance_80`.
4. Code exempt on `decided_on` (first permits and extensions), or any declared exemption →
   `salary_75_exempt`.
5. Otherwise `salary_90`.
Median: `median_on(filed_on)`, in force from its `effective_from` inclusive. The transition window
is inclusive at both ends. Threshold: `round_half_up(percent × median)`. Pass when
salary ≥ threshold.

## Search (`core/search.py`, extended)

**SearchRequest**: `text: str` (1–20 000 chars), `mode: "fast" | "full"` (default fast),
`k: int` (1–20, default 5), `parse_ad: bool` (default false).

**SearchHit** (001, extended): adds `legal_flags: list[LegalFlag]`.

**SearchAnswer**: `mode_used`, `fallback_reason: str | None`, `searched_text: str`,
`title_list: list[str] | None` (when the text was treated as alternatives, FR-013a),
`passages: list[AdPassage] | None` (when `parse_ad`), `low_confidence: bool`, `hits`,
`honest_fit: str`.

## Ad parsing (`core/adparse.py`)

**AdPassage**: `index: int`, `text: str`, `label: "title" | "duty" | "skill" | "company" |
"benefits" | "other"`, `keep: bool` (true for title, duty, skill), `by: "heading" | "anchor" |
"position"` (what decided the label).

**ParsedAd**: `passages`, `kept_text: str`, `fallback_to_whole: bool`.

## Salary payload (`core/salary.py`, extended)

**ThresholdLine**: `rule_id`, `percent`, `amount_sek`, `median`, `on: date`.

**SimulatedPercentiles**: `age_band`, `p10 … p90: int | None`, `is_simulated: Literal[True]`,
`formula: "percentile × age_band_mean ÷ all_ages_mean"`, `inputs: list[{table, reference_year}]`.
Any null input gives a null output.

**SalaryPayload**: `code`, `title_sv`, `title_en`, `distributions: list[SalaryDistribution]`
(every year, nulls kept), `age_bands: list[AgeBandSalary]` (latest year), `thresholds:
list[ThresholdLine]` (90 %, 75 %, and the code's own on the request date), `simulated:
SimulatedPercentiles | None`, `no_occupation_data: bool`.

## Comparison (`core/compare.py`)

**CompareRequest**: `codes: list[str]` (deduplicated, then 2–5), `offer: EligibilityRequest minus
code | None`.

**CompareColumn**: `code`, `titles`, `tasks_sv`, `tasks_en` (official descriptions), `latest:
SalaryDistribution | None`, `legal_flags`, `threshold: ThresholdLine`, `eligibility:
EligibilityAnswer | None`.

**Comparison**: `columns` (request order), `honest_fit: str`.

## Benchmark (`etl/benchmark.py`, extended)

Results file gains: `mode` (fast, full), `n` beside every metric, `diagnosis` (recall by language ×
origin × form, share of gap explained), `low_confidence_cutoff` with how it was chosen, and
`previous` (the 001 headline numbers) for comparison.
