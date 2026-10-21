import pytest

from lonekrav.core.benchmark import first_rank, mrr, recall_at


def test_first_rank_with_several_acceptable_codes():
    assert first_rank(["2511", "2512", "2514"], {"2514", "2512"}) == 2
    assert first_rank(["2511"], {"9999"}) is None


def test_recall_and_mrr_by_hand():
    ranks = [1, 3, None, 6]
    assert recall_at(ranks, 1) == pytest.approx(1 / 4)
    assert recall_at(ranks, 5) == pytest.approx(2 / 4)
    assert mrr(ranks) == pytest.approx((1 + 1 / 3 + 0 + 1 / 6) / 4)


def test_empty_is_not_a_division_error():
    assert recall_at([], 5) is None and mrr([]) is None


def test_diagnose_splits_the_gap_by_origin_and_form():  # FR-018
    from lonekrav.etl.benchmark import diagnose

    def q(qid, origin, text_sv, en, sv):  # fused ranks per language for one paired query
        return {"id": qid, "origin": origin, "form": "slash" if "/" in text_sv else "single",
                "paired": True, "ranks": {"en": {"fused": en}, "sv": {"fused": sv}}}

    rows = [
        q("a", "generated", "Aktuarie/Försäkringsaktuarie", 1, None),  # slash: EN hit, SV miss
        q("b", "generated", "Riksdagsledamot", 2, 9),                  # single: EN hit, SV miss
        q("c", "generated", "Departementsråd", 1, 1),                  # both hit
        q("d", "handwritten", "sjuksköterska", 3, 2),                  # both hit
    ]
    d = diagnose(rows, method="fused")
    assert d["gap"] == pytest.approx(0.5)  # EN 4/4 − SV 2/4
    g = {(r["origin"], r["form"]): r for r in d["groups"]}
    assert g[("generated", "slash")]["n"] == 1
    assert g[("generated", "slash")]["recall_at_5"] == {"en": 1.0, "sv": 0.0}
    assert g[("generated", "slash")]["gap_points"] == pytest.approx(0.25)
    assert g[("generated", "single")]["share_of_gap"] == pytest.approx(0.5)  # one of two misses
    assert g[("handwritten", "single")]["gap_points"] == 0
    assert sum(r["gap_points"] for r in d["groups"]) == pytest.approx(d["gap"])
