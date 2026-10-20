"""SCB PxWeb v2 salary tables (json-stat2)."""

from __future__ import annotations

import json
from pathlib import Path

NOT_OCCUPATIONS = {"0000", "0001", "0002"}  # all occupations, other, unknown


def occupation_labels(path: Path) -> dict[str, str]:
    """Swedish label per occupation code in a json-stat2 salary table."""
    labels = json.loads(path.read_text())["dimension"]["Yrke2012"]["category"]["label"]
    return {c: lab.strip() for c, lab in labels.items() if c not in NOT_OCCUPATIONS}
