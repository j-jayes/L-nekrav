"""Cross-lingual benchmark: query model and retrieval metrics."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class BenchmarkQuery(BaseModel):
    id: str
    origin: Literal["handwritten", "generated"]
    type: Literal["title", "duty_sentence", "description", "lookalike"]
    text_en: str | None = None
    text_sv: str
    expected_codes: list[str] = Field(min_length=1)


def load_handwritten(path: Path) -> list[BenchmarkQuery]:
    return [BenchmarkQuery(origin="handwritten", **q) for q in yaml.safe_load(path.read_text())]


def first_rank(ranked: Sequence[str], expected: set[str]) -> int | None:
    """1-based rank of the first acceptable code, or None if absent."""
    return next((i for i, c in enumerate(ranked, 1) if c in expected), None)


def recall_at(ranks: Sequence[int | None], k: int) -> float | None:
    return sum(r is not None and r <= k for r in ranks) / len(ranks) if ranks else None


def mrr(ranks: Sequence[int | None]) -> float | None:
    return sum(1 / r for r in ranks if r) / len(ranks) if ranks else None
