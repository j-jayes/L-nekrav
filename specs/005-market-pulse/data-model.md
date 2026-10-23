# Data model: Market pulse

All models are pydantic v2 and shared by every surface. Every field may be `null` where SCB or
JobTech publishes nothing; nothing is filled in.

## RegionalSalary (`core/models.py`, committed in `salary_regional.parquet`)

| Field | Type | Notes |
|---|---|---|
| code | str `^\d{4}$` | SSYK 2012 |
| year | int ≥ 2023 | |
| region | str | `SE`, or a national area `SE11`…`SE33` |
| region_name | str | SCB's English label |
| mean | int \| null | mean monthly salary, SEK |
| mean_ci95 | int \| null | ± margin of the 95 % CI, as published |
| employees | int \| null | estimated number of employees |
| source_table | `"TAB5696"` | |
| reference_year | int | equals `year` (validated) |
| fetched_at | datetime | from the raw file's meta |
| suppressed (computed) | list[str] | the fields among `mean`, `employees` that are null |

## YearlyAds (`core/models.py`, committed in `ad_history.parquet`)

| Field | Type | Notes |
|---|---|---|
| concept_id | str | JobTech occupation-group concept |
| year | int ≥ 2016 | full calendar years only |
| ads | int ≥ 0 | 0 is a real count |
| source | `"jobtech_historical"` | |
| built_at | datetime | when the build ran |

## LiveDemand (`core/market.py`, in memory, reused for 15 min)

| Field | Type | Notes |
|---|---|---|
| status | `available` \| `no_concept` \| `unavailable` | |
| concept_id | str \| null | null for `no_concept` |
| ads | int \| null | null unless `available` |
| positions | int \| null | null unless `available` |
| counties | list[CountyCount] | ordered by count, descending; empty unless `available` |
| no_county | int \| null | ads with no county (`total − Σcounties`) |
| reason | str \| null | for `unavailable`: `timeout`, `http 503`, `connection error`, `unexpected response` |
| fetched_at | datetime \| null | when the count was fetched (kept on reuse) |
| source | SourceRef | the JobSearch API, with the request URL |

`CountyCount`: `name` (Swedish county name, as JobTech gives it), `code` (the two-digit county
code), and `ads`.

## MarketAnswer (`core/market.py`)

| Field | Type | Notes |
|---|---|---|
| code, title_sv, title_en | str | |
| shared_with | list[str] | the other codes with the same concept (1211 ↔ 1212); empty if none |
| live | LiveDemand | |
| regional | list[RegionalSalary] | the latest year, `SE` first, then the areas by code; empty if the code is not in TAB5696 |
| regional_year | int \| null | |
| history | list[YearlyAds] | ascending by year; empty for `no_concept` |
| history_status | `available` \| `no_concept` | |
| notice | str | the honest-fit and mean-not-median statement (constant `MARKET_NOTICE`) |

## Relations

- `OccupationProfile.jobtech_concept_id` → `LiveDemand.concept_id` and `YearlyAds.concept_id`.
- `OccupationProfile.code` → `RegionalSalary.code`.
- `shared_with` is the set of profiles with the same `jobtech_concept_id`, minus the code itself.
