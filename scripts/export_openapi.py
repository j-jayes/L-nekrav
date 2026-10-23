"""Write the API's OpenAPI schema to frontend/src/api/openapi.json for the page's generated types.

    uv run python scripts/export_openapi.py && (cd frontend && npm run gen)

The schema comes from create_app() without its lifespan, so no model or index is loaded.
tests/integration/test_openapi_drift.py fails when the committed copy is stale (Feature 004 R6).
"""

import json
from pathlib import Path

from lonekrav.app import create_app

OUT = Path(__file__).parents[1] / "frontend" / "src" / "api" / "openapi.json"

if __name__ == "__main__":
    OUT.write_text(json.dumps(create_app().openapi(), indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {OUT}")
