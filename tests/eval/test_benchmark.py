"""The retrieval gate (constitution IV): run with `uv run pytest -m benchmark`.

Needs a built index with both models (`lonekrav-etl build && lonekrav-etl index`).
"""

import pytest

from lonekrav.etl import benchmark

pytestmark = pytest.mark.benchmark


@pytest.fixture(scope="module")
def result():
    return benchmark.run()


def test_fused_recall_at_5_at_least_80_percent_in_each_language(result):  # SC-004
    for lang in ("en", "sv"):
        assert result["metrics"]["fused"][lang]["all_paired"]["recall_at_5"] >= 0.80, lang


def test_language_gap_at_most_5_points(result):  # SC-005
    assert abs(result["gap_recall_at_5"]["fused"]["all_paired"]) <= 0.05


def test_fusion_at_least_as_good_as_each_method(result):  # SC-006
    m = result["metrics"]
    for lang in ("en", "sv"):
        fused = m["fused"][lang]["all_paired"]["recall_at_5"]
        for method in ("kblab", "harrier", "bm25"):
            assert fused >= m[method][lang]["all_paired"]["recall_at_5"], (lang, method)


def test_english_and_swedish_pairs_share_top5(result):  # spec story 3, scenario 2
    assert result["handwritten_top5_overlap_ge3"] >= 0.80
