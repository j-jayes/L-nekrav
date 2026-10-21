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


def test_low_confidence_cutoff_keeps_95_percent_above():  # FR-017a
    from lonekrav.etl.benchmark import choose_cutoff

    scores = [i / 100 for i in range(40, 100)]  # 60 benchmark queries: 0.40 … 0.99
    c = choose_cutoff(scores, nonsense=[0.10, 0.25])
    assert c["ok"] and c["cutoff"] == pytest.approx(0.43)  # 57 of 60 (95 %) at or above
    assert c["share_above"] >= 0.95 and c["nonsense_max"] == 0.25


def test_low_confidence_cutoff_reports_when_nonsense_scores_too_high():
    from lonekrav.etl.benchmark import choose_cutoff

    c = choose_cutoff([0.5, 0.6, 0.7, 0.8], nonsense=[0.65])
    assert not c["ok"] and c["cutoff"] is None and "nonsense" in c["note"]


def test_missing_top_score_counts_as_lowest():
    from lonekrav.etl.benchmark import choose_cutoff

    assert choose_cutoff([None, *([0.9] * 19)], nonsense=[0.1])["cutoff"] == pytest.approx(0.9)
