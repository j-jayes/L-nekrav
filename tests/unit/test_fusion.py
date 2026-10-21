import pytest

from lonekrav.core.search import RRF_K, ChunkHit, fuse, reduce_to_codes


def hit(code, score, kind="title"):
    return ChunkHit(chunk_id=f"{code}:{kind}:0", code=code, kind=kind, text=code, score=score)


def test_reduce_keeps_max_per_code_in_order():
    ranked = reduce_to_codes([hit("2512", 0.5, "desc_sv"), hit("2421", 0.7), hit("2512", 0.9)])
    assert [(c, round(h.score, 2)) for c, h in ranked] == [("2512", 0.9), ("2421", 0.7)]


def test_bm25_negative_distances_become_positive_scores():
    from lonekrav.core.store import bm25_score

    assert bm25_score(-2.5) == 2.5 and bm25_score(2.5) == 2.5


def test_rrf_order_and_missing_methods():
    per = {
        "kblab": [("A", hit("A", .9)), ("B", hit("B", .8))],
        "bm25": [("B", hit("B", 3.0)), ("C", hit("C", 2.0))],
    }
    hits = fuse(per, k=3)
    assert [h.code for h in hits] == ["B", "A", "C"]  # B: 1/62 + 1/61 beats A: 1/61
    b = hits[0]
    assert b.fused_rank == 1
    assert b.ranks == {"kblab": 2, "bm25": 1}
    assert b.fused_score == pytest.approx(1 / (RRF_K + 2) + 1 / (RRF_K + 1))
    c = hits[2]
    assert c.scores["kblab"] is None and c.ranks["kblab"] is None
    assert c.matched_chunk.kind == "title"
