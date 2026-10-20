from collections import Counter
from pathlib import Path

import pytest

from lonekrav.core.benchmark import load_handwritten

YAML = Path(__file__).parents[1] / "eval" / "queries_handwritten.yaml"
PROFILES = Path(__file__).parents[2] / "data" / "processed" / "ssyk_profiles.json"


def test_handwritten_set_shape():
    qs = load_handwritten(YAML)
    assert len(qs) >= 30
    assert set(Counter(q.type for q in qs)) == {"title", "duty_sentence", "description", "lookalike"}
    assert all(q.text_en and q.text_sv and q.expected_codes for q in qs)
    assert len({q.id for q in qs}) == len(qs)


@pytest.mark.skipif(not PROFILES.exists(), reason="needs data/processed (run lonekrav-etl build)")
def test_expected_codes_exist():
    from lonekrav.core.profiles import load_profiles

    codes = set(load_profiles(PROFILES))
    for q in load_handwritten(YAML):
        assert set(q.expected_codes) <= codes, q.id
