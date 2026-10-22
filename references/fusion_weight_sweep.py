"""Fusion-weight sweep (Feature 002, T020): fetch every paired query's chunk hits once with the real
models, cache them, then re-fuse with each weight grid point. Choose on generated queries, confirm
on hand-written ones (FR-020a). Usage: uv run python references/fusion_weight_sweep.py CACHE.pkl
Results: references/benchmark-diagnosis-002.md §2."""
import json
import pickle
import sys
from pathlib import Path

from lonekrav.core.benchmark import BenchmarkQuery, first_rank, load_handwritten
from lonekrav.core.embeddings import get_embedder
from lonekrav.core.search import POOL, SearchEngine, fuse, title_parts
from lonekrav.core.store import Store
from lonekrav.etl.benchmark import HANDWRITTEN

cache = Path(sys.argv[1])
qs = load_handwritten(HANDWRITTEN) + [BenchmarkQuery.model_validate(q) for q in
      json.loads(Path("data/processed/benchmark_generated.json").read_text())]
qs = [q for q in qs if q.text_en]  # paired only
if cache.exists():
    per = pickle.loads(cache.read_bytes())
else:
    M = ("kblab", "harrier", "bm25")
    e = SearchEngine(Store(), {m: get_embedder(m) for m in M if m != "bm25"}, {})
    per = {(q.id, lang): e.ranking(e.chunk_hits(title_parts(t) or [t], M, POOL), POOL)
           for q in qs for lang, t in (("en", q.text_en), ("sv", q.text_sv))}
    cache.write_bytes(pickle.dumps(per))

def score(subset, w):
    hit = {l: 0 for l in ("en", "sv")}; top = {}
    for q in subset:
        for l in ("en", "sv"):
            codes = [h.code for h in fuse(per[(q.id, l)], k=10, weights=w)]
            r = first_rank(codes, set(q.expected_codes)); hit[l] += r is not None and r <= 5
            top[(q.id, l)] = set(codes[:5])
    n = len(subset)
    ov = sum(len(top[(q.id, "en")] & top[(q.id, "sv")]) >= 3 for q in subset) / n
    return hit["en"] / n, hit["sv"] / n, ov

def single(subset, m):
    out = []
    for l in ("en", "sv"):
        out.append(sum((r := first_rank([c for c, _ in per[(q.id, l)][m][:10]], set(q.expected_codes))) is not None and r <= 5 for q in subset) / len(subset))
    return out

gen = [q for q in qs if q.origin == "generated"]; hw = [q for q in qs if q.origin == "handwritten"]
print("single methods (gen en/sv | hw en/sv):", {m: (single(gen, m), single(hw, m)) for m in ("kblab", "harrier", "bm25")})
rows = []
for wk in [x / 10 for x in range(11)]:
    for wb in [x / 10 for x in range(11)]:
        w = {"kblab": wk, "harrier": 1.0, "bm25": wb}
        ge, gs, _ = score(gen, w)
        rows.append((min(ge, gs), (ge + gs) / 2, wk, wb, ge, gs))
rows.sort(reverse=True)
print("top 10 on generated (min, mean, w_kblab, w_bm25, en, sv):")
for r in rows[:10]: print("  ", [round(x, 3) for x in r])
for wk, wb in [(1.0, 1.0)] + [(r[2], r[3]) for r in rows[:5]]:
    w = {"kblab": wk, "harrier": 1.0, "bm25": wb}
    print(f"w_kblab={wk} w_bm25={wb}: gen en/sv {score(gen, w)[:2]}  hw en/sv/overlap {score(hw, w)}  all {score(qs, w)}")
