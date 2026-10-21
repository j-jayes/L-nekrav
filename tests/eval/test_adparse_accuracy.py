"""Ad parsing on ten hand-labelled ads with the real KBLab model (spec SC-005).

Run with `uv run pytest -m benchmark tests/eval/test_adparse_accuracy.py`. The ads are made up
(tests/fixtures/ads/labels.yaml) until the JobTech licence allows real ones (research R5).
"""

from pathlib import Path

import pytest
import yaml

from lonekrav.core.adparse import parse
from lonekrav.core.search import SearchEngine, SearchRequest, run

pytestmark = pytest.mark.benchmark
ADS = Path(__file__).parents[1] / "fixtures" / "ads"
GOLD = yaml.safe_load((ADS / "labels.yaml").read_text())


@pytest.fixture(scope="module")
def engine():
    return SearchEngine.load()


def gold_label(text: str, passages: list) -> str | None:
    """The label of the longest gold prefix the passage starts with."""
    best = max((p for p in passages if text.startswith(p[0])), key=lambda p: len(p[0]),
               default=None)
    return best[1] if best else None


def test_passage_labels_agree_with_the_hand_labels(engine):
    right = total = 0
    wrong = []
    for name, ad in GOLD.items():
        for p in parse((ADS / name).read_text(), engine.embedders["kblab"]).passages:
            total += 1
            want = gold_label(p.text, ad["passages"])
            right += p.label == want
            if p.label != want:
                wrong.append((name, p.text[:50], p.label, want))
    print(f"\nagreement {right}/{total} = {right / total:.3f}")
    for w in wrong:
        print("  ", w)
    assert right / total >= 0.85


def test_kept_text_finds_the_code_at_least_as_often_as_the_raw_ad(engine):
    def hits(parse_ad):
        n = 0
        for name, ad in GOLD.items():
            a = run(SearchRequest(text=(ADS / name).read_text(), parse_ad=parse_ad), engine)
            top = [h.code for h in a.hits]
            n += bool(set(top) & set(ad["expected_codes"]))
            print(f"  parse_ad={parse_ad} {name}: {top} want {ad['expected_codes']}")
        return n

    raw, kept = hits(False), hits(True)
    print(f"\ntop-5 hits: raw ad {raw}/{len(GOLD)}, kept text {kept}/{len(GOLD)}")
    assert kept >= raw
