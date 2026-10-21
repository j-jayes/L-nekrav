"""Rank occupations for a query: per-method chunk search, reduce to codes, fuse with RRF.

Fusion runs after chunk scores are reduced to one score per occupation; Milvus's built-in
RRFRanker would fuse chunk lists, which is the wrong unit (research R7).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from functools import cache
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field

from lonekrav.core.embeddings import Embedder, get_embedder
from lonekrav.core.legal_flags import flags_for
from lonekrav.core.models import LegalFlag
from lonekrav.core.store import COLLECTION, FIELDS, Store

RRF_K = 60
POOL = 200  # chunks fetched per method before reducing to occupations
FAST_POOL = 50  # fast mode: research R2 (BM25 at 50 is 8 ms p95 against 16 at 200)
METHODS = ("kblab", "harrier", "bm25")
MODES = {"fast": ("kblab", "bm25"), "full": METHODS}
WEIGHTS: dict[str, float] = {"bm25": 0.3}  # chosen on generated queries, confirmed on
# hand-written ones (references/benchmark-diagnosis-002.md §2); a missing method counts 1.0
HONEST_FIT = ("The SSYK code on a work-permit offer must match the duties actually performed. "
              "These are the occupations whose official descriptions best match the text, not "
              "advice on which code to choose.")


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
    legal_flags: list[LegalFlag] = []


def reduce_to_codes(hits: Sequence[ChunkHit]) -> list[tuple[str, ChunkHit]]:
    """Best chunk per occupation, ordered by score (highest first)."""
    best: dict[str, ChunkHit] = {}
    for h in hits:
        if h.code not in best or h.score > best[h.code].score:
            best[h.code] = h
    return sorted(best.items(), key=lambda kv: (-kv[1].score, kv[0]))


def fuse(per_method: Mapping[str, list[tuple[str, ChunkHit]]], k: int = 5,
         weights: Mapping[str, float] | None = None) -> list[SearchHit]:
    weights = WEIGHTS if weights is None else weights
    methods = list(per_method)
    ranks = {m: {code: r for r, (code, _) in enumerate(lst, 1)} for m, lst in per_method.items()}
    chunks = {m: dict(lst) for m, lst in per_method.items()}
    codes = {c for lst in per_method.values() for c, _ in lst}
    scored = []
    for code in codes:
        fused = sum(weights.get(m, 1.0) / (RRF_K + ranks[m][code])
                    for m in methods if code in ranks[m])
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


_SENTENCE = re.compile(r"[.!?\n]")
MAX_TITLE_WORDS = 6
PAGE = 4000  # rows per query when loading vectors


def title_parts(text: str) -> list[str] | None:
    """A slash-joined list of titles ("Aktuarie/Försäkringsaktuarie"), split into its parts, or
    None for anything else: prose, multi-line text, or a part longer than a title (FR-013a)."""
    if "/" not in text or _SENTENCE.search(text):
        return None
    parts = [p.strip() for p in text.split("/")]
    if len(parts) < 2 or any(not p or len(p.split()) > MAX_TITLE_WORDS for p in parts):
        return None
    return parts


class SearchRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20_000)
    mode: Literal["fast", "full"] = "fast"
    k: int = Field(5, ge=1, le=20)


class SearchAnswer(BaseModel):
    mode_used: Literal["fast", "full"]
    fallback_reason: str | None = None
    searched_text: str
    title_list: list[str] | None = None
    low_confidence: bool
    hits: list[SearchHit]
    honest_fit: str = HONEST_FIT


class SearchEngine:
    """Everything a search needs, loaded once per process: the store, the embedders, titles, and
    each model's chunk vectors as an in-memory matrix (research R2: a matrix product over 9 556
    chunks takes 0.5 ms where Milvus Lite's FLAT search takes 26). The store stays the source of
    truth, so a Milvus server (MILVUS_URI) works the same way."""

    def __init__(self, store: Store, embedders: Mapping[str, Embedder],
                 titles: Mapping[str, tuple[str, str]],
                 harrier_loader: Callable[[], Embedder] | None = None,
                 low_confidence_cutoff: float | None = None):
        self.store, self.embedders, self.titles = store, dict(embedders), titles
        self.harrier_loader = harrier_loader or (lambda: get_embedder("harrier"))
        self.low_confidence_cutoff = low_confidence_cutoff
        self._load_vectors()

    @classmethod
    def load(cls) -> SearchEngine:
        from lonekrav.etl.benchmark import load_cutoff

        return cls(store=Store(), embedders={"kblab": get_embedder("kblab")}, titles=_titles(),
                   low_confidence_cutoff=load_cutoff())

    def _load_vectors(self) -> None:
        schema = self.store.client.describe_collection(COLLECTION)
        vec = [f["name"] for f in schema["fields"] if f["name"].startswith("vec_")]
        meta, cols = [], {v: [] for v in vec}
        # Milvus Lite has no query_iterator; page with offset (Milvus caps offset + limit at 16 384).
        offset = 0
        while batch := self.store.client.query(COLLECTION, filter="", limit=PAGE, offset=offset,
                                               output_fields=[*FIELDS, *vec]):
            for row in batch:
                meta.append({f: row[f] for f in FIELDS})
                for v in vec:
                    cols[v].append(row[v])
            offset += len(batch)
            if len(batch) < PAGE:
                break
        self._meta = meta
        self._matrix = {}
        for v, rows in cols.items():
            m = np.asarray(rows, dtype=np.float32)
            self._matrix[v.removeprefix("vec_")] = m / np.linalg.norm(m, axis=1, keepdims=True)

    def search_dense(self, name: str, vector: np.ndarray, limit: int) -> list[dict]:
        scores = self._matrix[name] @ (vector / np.linalg.norm(vector))
        top = np.argpartition(-scores, min(limit, len(scores) - 1))[:limit]
        top = top[np.argsort(-scores[top], kind="stable")]
        return [{**self._meta[i], "score": float(scores[i])} for i in top]

    def _ensure_harrier(self) -> str | None:
        """Load Harrier for full mode; the reason it is unavailable, or None."""
        if "harrier" not in self._matrix:
            return "the index has no Harrier vectors"
        if "harrier" not in self.embedders:
            try:
                self.embedders["harrier"] = self.harrier_loader()
            except Exception as e:  # noqa: BLE001 - any load failure degrades to fast mode (FR-014)
                return f"Harrier could not be loaded ({type(e).__name__})"
        return None

    def chunk_hits(self, queries: Sequence[str], methods: Sequence[str],
                   pool: int) -> dict[str, list[list[dict]]]:
        """Each method's top `pool` chunks for each query, best first. The top n chunks are a
        prefix of the top `pool`, so one fetch serves any smaller pool (the benchmark's fast mode)."""
        out = {}
        for m in methods:
            if m == "bm25":
                out[m] = [self.store.search_bm25(q, pool) for q in queries]
            else:
                vecs = self.embedders[m].encode_queries(list(queries))
                out[m] = [self.search_dense(m, v, pool) for v in vecs]
        return out

    @staticmethod
    def ranking(hits: Mapping[str, list[list[dict]]],
                pool: int) -> dict[str, list[tuple[str, ChunkHit]]]:
        """Per method, occupations ranked by their best chunk among every query's top `pool`."""
        return {m: reduce_to_codes([ChunkHit(**h) for per_q in lists for h in per_q[:pool]])
                for m, lists in hits.items()}

    def fused(self, per: Mapping[str, list[tuple[str, ChunkHit]]], k: int) -> list[SearchHit]:
        hits = fuse(per, k=k)
        for h in hits:
            h.title_sv, h.title_en = self.titles.get(h.code, ("", ""))
            h.legal_flags = flags_for(h.code)
        return hits

    def rank(self, text: str, methods: Sequence[str], pool: int,
             k: int) -> tuple[list[SearchHit], list[str] | None]:
        """Fused top-k for a text; a title list searches each part and pools the chunk hits."""
        parts = title_parts(text)
        per = self.ranking(self.chunk_hits(parts or [text], methods, pool), pool)
        return self.fused(per, k), parts


def run(req: SearchRequest, engine: SearchEngine) -> SearchAnswer:
    mode, reason = req.mode, None
    if mode == "full" and (reason := engine._ensure_harrier()):
        mode = "fast"
    hits, parts = engine.rank(req.text, MODES[mode], FAST_POOL if mode == "fast" else POOL, req.k)
    cutoff = engine.low_confidence_cutoff
    top = hits[0].scores.get("kblab") if hits else None
    low = cutoff is not None and (top is None or top < cutoff)
    return SearchAnswer(mode_used=mode, fallback_reason=reason, searched_text=req.text,
                        title_list=parts, low_confidence=low, hits=hits)
