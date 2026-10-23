"""The page's types are generated from a committed copy of the API schema (Feature 004 R6)."""

import json
from pathlib import Path

COMMITTED = Path(__file__).parents[2] / "frontend" / "src" / "api" / "openapi.json"
REGENERATE = "run: uv run python scripts/export_openapi.py, then npm run gen in frontend/"


def test_committed_schema_matches_the_app():
    from lonekrav.app import create_app

    assert COMMITTED.is_file(), REGENERATE
    assert json.loads(COMMITTED.read_text()) == create_app().openapi(), REGENERATE
