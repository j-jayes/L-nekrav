# HTTP contract: market

## `GET /api/v1/occupations/{code}/market`

- **200**: a `MarketAnswer` (data-model.md). This is always 200 for a known code, whatever the
  state of JobSearch. A live failure shows as `live.status = "unavailable"`, never as a 5xx.
- **404**: `{"detail": "unknown SSYK code: 9999"}`, as for `/salary`.

Example, abridged and with the live numbers from the 2026-10-23 probe:

```json
{
  "code": "2512", "title_sv": "Mjukvaru- och systemutvecklare m.fl.", "title_en": "Software and system developers",
  "shared_with": [],
  "live": {"status": "available", "concept_id": "DJh5_yyF_hEM", "ads": 1183, "positions": 1569,
           "counties": [{"name": "Stockholms län", "code": "01", "ads": 488}, "..."],
           "no_county": 0, "reason": null, "fetched_at": "2026-10-23T09:12:00Z",
           "source": {"source": "jobtech_jobsearch", "ref": "occupation-group=DJh5_yyF_hEM",
                      "url": "https://jobsearch.api.jobtechdev.se/search?occupation-group=DJh5_yyF_hEM&limit=0&stats=region&stats.limit=30"}},
  "regional_year": 2025,
  "regional": [{"region": "SE", "region_name": "Sweden", "mean": 55500, "mean_ci95": 940, "employees": 113100, "source_table": "TAB5696", "...": "..."},
               {"region": "SE21", "region_name": "Småland and islands", "mean": 48400, "mean_ci95": 1960, "employees": null, "suppressed": ["employees"], "...": "..."}],
  "history_status": "available",
  "history": [{"concept_id": "DJh5_yyF_hEM", "year": 2016, "ads": 16406, "source": "jobtech_historical", "fetched_at": "..."}, "..."],
  "notice": "..."
}
```

`Source` gains `jobtech_jobsearch` and `jobtech_historical`.
