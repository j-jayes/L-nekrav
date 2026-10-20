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
