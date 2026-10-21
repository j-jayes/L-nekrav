"""Rank occupations for a query: per-method chunk search, reduce to codes, fuse with RRF.

Fusion runs after chunk scores are reduced to one score per occupation; Milvus's built-in
RRFRanker would fuse chunk lists, which is the wrong unit (research R7).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from functools import cache

from pydantic import BaseModel

from lonekrav.core.embeddings import Embedder, get_embedder
from lonekrav.core.store import Store

RRF_K = 60
POOL = 200  # chunks fetched per method before reducing to occupations
METHODS = ("kblab", "harrier", "bm25")


class ChunkHit(BaseModel):
    chunk_id: str
    code: str
    kind: str
    text: str
    score: float


class MatchedChunk(BaseModel):
    kind: str
    text: str


class SearchHit(BaseModel):
    code: str
    title_sv: str = ""
    title_en: str = ""
    scores: dict[str, float | None]
    ranks: dict[str, int | None]
    fused_score: float
    fused_rank: int
    matched_chunk: MatchedChunk


def reduce_to_codes(hits: Sequence[ChunkHit]) -> list[tuple[str, ChunkHit]]:
    """Best chunk per occupation, ordered by score (highest first)."""
    best: dict[str, ChunkHit] = {}
    for h in hits:
        if h.code not in best or h.score > best[h.code].score:
            best[h.code] = h
    return sorted(best.items(), key=lambda kv: (-kv[1].score, kv[0]))


def fuse(per_method: Mapping[str, list[tuple[str, ChunkHit]]], k: int = 5) -> list[SearchHit]:
    methods = list(per_method)
    ranks = {m: {code: r for r, (code, _) in enumerate(lst, 1)} for m, lst in per_method.items()}
    chunks = {m: dict(lst) for m, lst in per_method.items()}
    codes = {c for lst in per_method.values() for c, _ in lst}
    scored = []
    for code in codes:
        fused = sum(1 / (RRF_K + ranks[m][code]) for m in methods if code in ranks[m])
        top = min((m for m in methods if code in ranks[m]), key=lambda m: ranks[m][code])
        scored.append((fused, code, top))
    scored.sort(key=lambda t: (-t[0], t[1]))
    out = []
    for i, (fused, code, top) in enumerate(scored[:k], 1):
        best = chunks[top][code]
        out.append(SearchHit(
            code=code,
            scores={m: chunks[m][code].score if code in chunks[m] else None for m in methods},
            ranks={m: ranks[m].get(code) for m in methods},
            fused_score=fused, fused_rank=i,
            matched_chunk=MatchedChunk(kind=best.kind, text=best.text),
        ))
    return out


@cache
def _titles() -> dict[str, tuple[str, str]]:
    """Titles for display, read once per process (the profiles file is ~19 MB)."""
    from lonekrav.core import profiles

    return {c: (p.title_sv, p.title_en) for c, p in profiles.load_profiles().items()}


def search(
    query: str,
    *,
    methods: Sequence[str] = METHODS,
    k: int = 5,
    store: Store | None = None,
    embedders: Mapping[str, Embedder] | None = None,
    titles: Mapping[str, tuple[str, str]] | None = None,
) -> list[SearchHit]:
    """Top-k occupations. `methods=("kblab", "bm25")` is the fast path for live typing."""
    store = store or Store()
    per: dict[str, list[tuple[str, ChunkHit]]] = {}
    for m in methods:
        if m == "bm25":
            raw = store.search_bm25(query, POOL)
        else:
            emb = (embedders or {}).get(m) or get_embedder(m)
            raw = store.search_dense(m, emb.encode_queries([query])[0], POOL)
        per[m] = reduce_to_codes([ChunkHit(**h) for h in raw])
    hits = fuse(per, k=k)
    titles = _titles() if titles is None else titles
    for h in hits:
        h.title_sv, h.title_en = titles.get(h.code, ("", ""))
    return hits


class SearchEngine:
    """Everything a search needs, loaded once per process: the store, the embedders and titles."""

    def __init__(self, store: Store, embedders: Mapping[str, Embedder],
                 titles: Mapping[str, tuple[str, str]]):
        self.store, self.embedders, self.titles = store, dict(embedders), titles

    @classmethod
    def load(cls) -> SearchEngine:
        return cls(store=Store(), embedders={"kblab": get_embedder("kblab")}, titles=_titles())
