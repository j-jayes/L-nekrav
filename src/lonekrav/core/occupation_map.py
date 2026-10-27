"""The occupation map (Feature 007): one vector per SSYK code from its title and description
chunks, exact neighbours by cosine, and how close any two codes are. The 2-D positions are drawn
by the ETL (`lonekrav-etl map`, which needs UMAP); serving only reads the two artefacts written
here, which hold codes and numbers, never text.
"""

from __future__ import annotations

import bisect
import json
from collections.abc import Callable
from pathlib import Path

import numpy as np
import polars as pl
from pydantic import BaseModel

from lonekrav.core.chunks import Chunk

MAP = Path("data/processed/occupation_map.json")
SIMILARITY = Path("data/processed/occupation_similarity.parquet")
POOL_KINDS = ("title", "desc_sv", "desc_en")  # synonym lists are noisy; ILO chunks are never used
SAME_DESCRIPTION = 0.99  # at or above this, two codes share their official description (R2)
K = 10
HONEST_SIMILAR = ("The SSYK code on a work-permit offer must match the duties actually performed. "
                  "Similar official descriptions are context, not advice on which code to choose.")


class Neighbour(BaseModel):
    code: str
    cosine: float


class MapPoint(BaseModel):
    code: str
    x: float
    y: float
    major_group: str
    chunks: int  # how many chunks the code's vector was built from
    neighbours: list[Neighbour]


class OccupationMap(BaseModel):
    model: str
    chunk_kinds: list[str]
    ilo_excluded: bool
    chunk_set_sha256: str
    umap: dict[str, str | int | float]
    built_on: str
    pair_quantiles: list[float]  # the 0th-100th percentiles of every pair's cosine
    major_groups: dict[str, dict[str, str]]  # first digit -> {"sv", "en"} name, from SCB's files
    points: list[MapPoint]
    stale: bool = False  # set at load when the map was built with another model than the index's


class Closeness(BaseModel):
    a: str
    b: str
    cosine: float
    percentile: int | None  # the share of code pairs less similar; null when same_description
    same_description: bool
    honest_fit: str = HONEST_SIMILAR


def pool(chunks: list[Chunk], vector: Callable[[str], np.ndarray]
         ) -> tuple[list[str], np.ndarray, dict[str, int]]:
    """Codes in order, one L2-normalised mean vector per code, and the chunks each was built from."""
    rows: dict[str, list[np.ndarray]] = {}
    for c in chunks:
        if c.kind in POOL_KINDS and not c.ilo:
            rows.setdefault(c.code, []).append(vector(c.text))
    codes = sorted(rows)
    means = np.stack([np.mean(rows[c], axis=0) for c in codes]).astype(np.float32)
    return codes, means / np.linalg.norm(means, axis=1, keepdims=True), {c: len(rows[c]) for c in codes}


def neighbours(codes: list[str], X: np.ndarray, k: int = K) -> dict[str, list[Neighbour]]:
    S = X @ X.T
    np.fill_diagonal(S, -np.inf)
    order = np.argsort(-S, axis=1, kind="stable")[:, :min(k, len(codes) - 1)]  # never itself
    return {c: [Neighbour(code=codes[j], cosine=round(float(S[i, j]), 3)) for j in order[i]]
            for i, c in enumerate(codes)}


def pair_quantiles(S: np.ndarray) -> list[float]:
    pairs = S[np.triu_indices(len(S), 1)]
    return [round(float(v), 4) for v in np.percentile(pairs, np.arange(101))]


def percentile(cosine: float, quantiles: list[float]) -> int:
    """The share of code pairs less similar than `cosine`, to a whole per cent."""
    return min(100, max(0, bisect.bisect_right(quantiles, cosine) - 1))


def closeness(a: str, b: str, cosine: float, quantiles: list[float]) -> Closeness:
    same = cosine >= SAME_DESCRIPTION
    return Closeness(a=a, b=b, cosine=round(cosine, 3), same_description=same,
                     percentile=None if same else percentile(cosine, quantiles))


def write_map(m: OccupationMap, path: Path = MAP) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(m.model_dump(exclude={"stale"}), ensure_ascii=False, indent=1) + "\n")


def load_map(path: Path = MAP) -> OccupationMap:
    return OccupationMap.model_validate_json(path.read_text())


def write_similarity(codes: list[str], X: np.ndarray, path: Path = SIMILARITY) -> None:
    S = X @ X.T
    i, j = np.triu_indices(len(codes), 1)
    pl.DataFrame({"code_a": [codes[k] for k in i], "code_b": [codes[k] for k in j],
                  "cosine": S[i, j].astype(np.float32)}).write_parquet(path, statistics=False)


def load_similarity(path: Path = SIMILARITY) -> dict[tuple[str, str], float]:
    """Keyed by the ordered pair (code_a < code_b)."""
    df = pl.read_parquet(path)
    return dict(zip(zip(df["code_a"], df["code_b"], strict=True), df["cosine"].to_list(), strict=True))


# --- what is served (Service adds titles, medians and flags, which the artefact never holds) ----

class SimilarCode(BaseModel):
    code: str
    title_sv: str | None
    title_en: str | None
    cosine: float
    percentile: int | None  # the share of code pairs less similar; null when same_description
    same_description: bool
    median_sek: int | None  # SCB's latest published median; context, never a reason to pick
    median_year: int | None


class NeighbourAnswer(BaseModel):
    code: str
    neighbours: list[SimilarCode]  # nearest first, by similarity of the official descriptions
    honest_fit: str = HONEST_SIMILAR


class ServedPoint(MapPoint):
    title_sv: str | None
    title_en: str | None
    median_sek: int | None
    median_year: int | None
    legal_flags: list[str]  # the flag kinds, as in search results


class MapAnswer(BaseModel):
    model: str
    umap: dict[str, str | int | float]
    built_on: str
    stale: bool
    pair_quantiles: list[float]
    major_groups: dict[str, dict[str, str]]
    points: list[ServedPoint]
    honest_fit: str = HONEST_SIMILAR
