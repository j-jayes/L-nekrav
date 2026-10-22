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
    hits = fuse(per, k=3, weights={})  # plain RRF
    assert [h.code for h in hits] == ["B", "A", "C"]  # B: 1/62 + 1/61 beats A: 1/61
    b = hits[0]
    assert b.fused_rank == 1
    assert b.ranks == {"kblab": 2, "bm25": 1}
    assert b.fused_score == pytest.approx(1 / (RRF_K + 2) + 1 / (RRF_K + 1))
    c = hits[2]
    assert c.scores["kblab"] is None and c.ranks["kblab"] is None
    assert c.matched_chunk.kind == "title"


def test_weights_scale_each_methods_rrf_term():  # research R1, T018
    per = {"kblab": [("A", hit("A", 0.9)), ("B", hit("B", 0.8))],
           "bm25": [("B", hit("B", 9.0)), ("A", hit("A", 8.0))]}
    unweighted = [h.model_dump() for h in fuse(per, k=2, weights={})]
    assert [h.model_dump() for h in fuse(per, k=2, weights={"kblab": 1, "bm25": 1})] == unweighted
    weighted = fuse(per, k=2, weights={"bm25": 0.5})
    a = next(h for h in weighted if h.code == "A")
    assert a.fused_score == pytest.approx(1 / (RRF_K + 1) + 0.5 / (RRF_K + 2))
    assert [h.code for h in weighted] == ["A", "B"]  # kblab's order wins once bm25 counts half


def test_an_ilo_chunk_ranks_but_the_best_other_chunk_is_shown():  # Feature 004
    ilo = hit("A", 0.9, "desc_en").model_copy(update={"ilo": True, "text": "ILO task text"})
    esco = hit("A", 0.6, "desc_en").model_copy(update={"text": "ESCO text"})
    per = {"kblab": reduce_to_codes([ilo, esco])}
    shown = {"kblab": {"A": esco}}
    (a,) = fuse(per, k=1, weights={}, shown=shown)
    assert a.scores["kblab"] == 0.9  # ranked on the ILO chunk
    assert a.matched_chunk.text == "ESCO text"


def test_with_no_other_chunk_the_title_is_shown():
    ilo = hit("A", 0.9, "desc_en").model_copy(update={"ilo": True, "text": "ILO task text"})
    (a,) = fuse({"kblab": reduce_to_codes([ilo])}, k=1, weights={}, shown={})
    assert a.matched_chunk.kind == "title" and "ILO" not in a.matched_chunk.text
