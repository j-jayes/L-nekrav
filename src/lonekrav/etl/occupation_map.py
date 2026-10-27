"""`lonekrav-etl map`: the occupation map from the index's vector cache (Feature 007, research R1-R4).

Reads the cached Harrier vectors by text hash (no model is loaded), pools them per code with
`core.occupation_map.pool`, and draws 2-D positions with UMAP. UMAP is in the `map` dependency
group only, so run it as `uv run --group map lonekrav-etl map`. Its output is reproducible on one
machine but not byte-stable across platforms, so the map is rebuilt only on purpose, never by
`build`.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path

import numpy as np

from lonekrav.core.chunks import chunk_profile
from lonekrav.core.models import OccupationProfile
from lonekrav.core.occupation_map import (
    MAP,
    POOL_KINDS,
    SIMILARITY,
    MapPoint,
    OccupationMap,
    neighbours,
    pair_quantiles,
    pool,
    write_map,
    write_similarity,
)

UMAP = {"n_neighbors": 15, "min_dist": 0.1, "metric": "cosine", "random_state": 0}


def _umap(params: dict) -> tuple[Callable[[np.ndarray], np.ndarray], str]:
    """UMAP with fixed parameters on one thread (reproducible with a seed), and its version."""
    try:
        import umap
    except ImportError as e:
        raise ImportError("UMAP is not installed: run `uv run --group map lonekrav-etl map`") from e

    def reduce(X: np.ndarray) -> np.ndarray:
        return umap.UMAP(**params, n_jobs=1).fit_transform(X)
    return reduce, umap.__version__


def _unit(Y: np.ndarray) -> np.ndarray:
    """Into [0, 1] with one scale for both axes, so the picture keeps its shape."""
    Y = Y - Y.min(axis=0)
    return Y / Y.max()


def build_map(profiles: dict[str, OccupationProfile], cache: Path, identity: str, built_on: str,
              groups: dict[str, dict[str, str]],
              reduce: Callable[[np.ndarray], np.ndarray] | None = None,
              out_dir: Path | None = None) -> OccupationMap:
    with np.load(cache) as z:
        vectors = dict(zip(z["keys"].tolist(), z["vectors"], strict=True))

    def vector(text: str) -> np.ndarray:
        key = hashlib.sha256(text.encode()).hexdigest()
        if key not in vectors:
            raise KeyError(f"no cached vector for a chunk in {cache}: run `lonekrav-etl index` first")
        return vectors[key]

    chunks = [c for p in profiles.values() for c in chunk_profile(p)]
    used = sorted(c.chunk_id for c in chunks if c.kind in POOL_KINDS and not c.ilo)
    codes, X, counts = pool(chunks, vector)
    params = {**UMAP, "n_neighbors": min(UMAP["n_neighbors"], len(codes) - 1)}
    if reduce is None:
        reduce, params["umap_version"] = _umap(dict(params))  # the version is recorded, not passed
    Y = _unit(reduce(X))
    near = neighbours(codes, X)
    m = OccupationMap(
        model=identity, chunk_kinds=list(POOL_KINDS), ilo_excluded=True,
        chunk_set_sha256=hashlib.sha256("\n".join(used).encode()).hexdigest(), umap=params,
        built_on=built_on, pair_quantiles=pair_quantiles(X @ X.T), major_groups=groups,
        points=[MapPoint(code=c, x=round(float(Y[i, 0]), 4), y=round(float(Y[i, 1]), 4),
                         major_group=c[0], chunks=counts[c], neighbours=near[c])
                for i, c in enumerate(codes)])
    out = out_dir or MAP.parent
    out.mkdir(parents=True, exist_ok=True)
    write_map(m, out / MAP.name)
    write_similarity(codes, X, out / SIMILARITY.name)
    return m
