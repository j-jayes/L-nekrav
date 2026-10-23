# Quickstart: validate Market pulse

## Prerequisites

The 004 setup (index built, `frontend/` installed). Network access for the fetch and live steps.

## Build the data

```bash
uv run lonekrav-etl fetch --only scb_pxweb jobsearch_history   # TAB5696 + ~3 970 cached history files
uv run lonekrav-etl build                                      # writes salary_regional + ad_history parquet
data-dict validate-data data/processed/data-dict.yaml
```

Expected: the build prints regional rows and history rows, and fails if any concept-year is
missing.

## Tests

```bash
rtk proxy uv run pytest -q              # offline; new market tests included
uv run pytest -m live -k market         # one real JobSearch call
(cd frontend && npm test && npm run build)
```

## By hand

```bash
PORT=8010 uv run lonekrav-serve &
curl -s 127.0.0.1:8010/api/v1/occupations/2512/market | jq '.live.status, .live.ads, .regional[0], .history[-1]'
curl -s 127.0.0.1:8010/api/v1/occupations/1211/market | jq '.shared_with'     # ["1212"]
curl -s 127.0.0.1:8010/api/v1/occupations/4430/market | jq '.live.status'     # "no_concept"
curl -s 'https://jobsearch.api.jobtechdev.se/search?occupation-group=DJh5_yyF_hEM&limit=0' | jq .total   # same as .live.ads
```

- **Unavailable**: run the server with `LONEKRAV_JOBSEARCH_URL=http://127.0.0.1:9` and confirm
  `live.status` is `unavailable` within 5 s (SC-003). This setting exists only so the failure
  path can be tested by hand and in e2e.
- **Page**: open `/?view=compare&codes=2512,2511` and take screenshots at 390 and 1280 px (SC-006).

Record the results in `references/market-pulse.md`.
