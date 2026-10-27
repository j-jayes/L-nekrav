# Quickstart: validate Occupation map

```bash
uv run --group map lonekrav-etl map          # about 10 s; writes occupation_map.json and occupation_similarity.parquet
data-dict validate-data data/processed/data-dict.yaml
rtk proxy uv run pytest -q                   # the UMAP test is skipped without the map group
uv run --group map pytest tests/unit/test_occupation_map.py
PORT=8010 uv run lonekrav-serve &
curl -s 127.0.0.1:8010/api/v1/occupations/2511/neighbours | jq '[.neighbours[:3][] | .code]'   # contains 2512, 2519
curl -s '127.0.0.1:8010/api/v1/closeness?a=1311&b=1312' | jq .same_description                # true
(cd frontend && npm test && BASE_URL=http://127.0.0.1:8010 npx playwright test e2e/views.spec.ts)
LONEKRAV_PORT=8001 docker compose up --build -d && docker compose exec app python -c "import umap" # must fail
```

Record the screenshots, the SC-003 preservation figure and the image size difference in
`references/occupation-map.md`.
