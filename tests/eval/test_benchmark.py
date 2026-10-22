"""The retrieval gate (constitution IV; spec FR-020, FR-020a): run with `uv run pytest -m benchmark`.

Needs a built index with both models (`lonekrav-etl build && lonekrav-etl index`). Full mode
("fused") must pass every gate on all paired queries; fast mode ("fused_fast") must keep Recall@5
at 0.80 or above in each language.
"""

import pytest

from lonekrav.etl import benchmark

pytestmark = pytest.mark.benchmark
LANGS = ("en", "sv")


@pytest.fixture(scope="module")
def result():
    return benchmark.run()


def paired(result, method, lang, metric="recall_at_5"):
    return result["metrics"][method][lang]["all_paired"][metric]


def test_enough_paired_queries_for_the_gap_to_mean_something(result):  # FR-020a
    assert paired(result, "fused", "en", "n") >= 60


def test_full_mode_recall_at_5_at_least_80_percent_in_each_language(result):
    for lang in LANGS:
        assert paired(result, "fused", lang) >= 0.80, lang


def test_full_mode_language_gap_at_most_5_points(result):
    assert abs(result["gap_recall_at_5"]["fused"]["all_paired"]) <= 0.05


def test_full_mode_fusion_at_least_as_good_as_each_method(result):
    for lang in LANGS:
        for method in ("kblab", "harrier", "bm25"):
            assert paired(result, "fused", lang) >= paired(result, method, lang), (lang, method)


def test_handwritten_pairs_share_top5_in_full_mode(result):
    assert result["handwritten_top5_overlap_ge3"] >= 0.80


def test_fast_mode_recall_at_5_at_least_80_percent_in_each_language(result):
    for lang in LANGS:
        assert paired(result, "fused_fast", lang) >= 0.80, lang


def test_low_confidence_cutoff_separates_nonsense(result):  # FR-017a
    assert result["low_confidence"]["ok"], result["low_confidence"]["note"]
