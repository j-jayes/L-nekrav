"""Search engine modes, title lists, legal flags and honest-fit text on the fixture index (Story 2)."""

import pytest

from lonekrav.core.search import HONEST_FIT, SearchRequest, run


def test_dense_matrix_matches_the_store(fixture_engine):
    engine, _ = fixture_engine
    v = engine.embedders["kblab"].encode_queries(["mjukvaruutvecklare"])[0]
    mem, db = engine.search_dense("kblab", v, 10), engine.store.search_dense("kblab", v, 10)
    assert [round(h["score"], 5) for h in mem] == [round(h["score"], 5) for h in db]
    cut = round(db[-1]["score"], 5)  # the FakeEmbedder ties a lot; compare above the last score
    assert ({h["chunk_id"] for h in mem if round(h["score"], 5) > cut}
            == {h["chunk_id"] for h in db if round(h["score"], 5) > cut})


def test_fast_mode_uses_kblab_and_bm25(fixture_engine):
    engine, _ = fixture_engine
    a = run(SearchRequest(text="mjukvaruutvecklare", mode="fast"), engine)
    assert a.mode_used == "fast" and a.fallback_reason is None
    assert a.hits and set(a.hits[0].scores) == {"kblab", "bm25"}
    assert a.honest_fit == HONEST_FIT and a.searched_text == "mjukvaruutvecklare"


def test_full_mode_falls_back_when_harrier_cannot_load(fixture_engine):
    engine, _ = fixture_engine

    def broken():
        raise OSError("model download failed")

    engine.harrier_loader = broken
    a = run(SearchRequest(text="mjukvaruutvecklare", mode="full"), engine)
    assert a.mode_used == "fast" and "harrier" in a.fallback_reason.lower()
    assert a.hits


def test_title_list_pools_the_parts(fixture_engine):
    engine, _ = fixture_engine
    a = run(SearchRequest(text="Mjukvaruutvecklare/Drifttekniker", k=10), engine)
    assert a.title_list == ["Mjukvaruutvecklare", "Drifttekniker"]
    codes = [h.code for h in a.hits]
    assert "2512" in codes and "3511" in codes  # each part finds its own occupation


def test_hits_carry_registry_legal_flags(fixture_engine):
    engine, _ = fixture_engine
    a = run(SearchRequest(text="drifttekniker", k=10), engine)
    flagged = {h.code: [f.kind for f in h.legal_flags] for h in a.hits}
    assert flagged.get("3511") == ["exempt_75"]
    assert all(f.checked_on for h in a.hits for f in h.legal_flags)


@pytest.mark.parametrize("text", ["mjukvaruutvecklare", "drifttekniker", "personlig assistent"])
def test_hits_are_ordered_by_fused_score_never_by_threshold(fixture_engine, text):  # SC-007
    engine, _ = fixture_engine
    a = run(SearchRequest(text=text, k=10), engine)
    scores = [h.fused_score for h in a.hits]
    assert scores == sorted(scores, reverse=True)
    assert not {"threshold", "threshold_sek", "salary"} & set(a.hits[0].model_dump())


def test_low_confidence_below_the_cutoff(fixture_engine):
    engine, _ = fixture_engine
    engine.low_confidence_cutoff = 2.0  # above any cosine: everything is low confidence
    assert run(SearchRequest(text="mjukvaruutvecklare"), engine).low_confidence
    engine.low_confidence_cutoff = -1.0
    assert not run(SearchRequest(text="mjukvaruutvecklare"), engine).low_confidence


@pytest.mark.parametrize("body", [{"text": ""}, {"text": "x" * 20001}, {"text": "a", "k": 21},
                                  {"text": "a", "mode": "slow"}])
def test_invalid_search_requests(body):
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        SearchRequest(**body)


def test_benchmark_ranks_through_the_live_search_path(fixture_engine):  # FR-017, T037
    from lonekrav.core.benchmark import BenchmarkQuery
    from lonekrav.core.search import POOL
    from lonekrav.etl.benchmark import evaluate

    engine, _ = fixture_engine
    q = BenchmarkQuery(id="t", origin="handwritten", type="title", text_en="software developer",
                       text_sv="Mjukvaruutvecklare/Drifttekniker", expected_codes=["2512"])
    result = evaluate([q], engine, ("kblab", "bm25"))
    for lang, text in (("en", q.text_en), ("sv", q.text_sv)):
        live, _ = engine.rank(text, ("kblab", "bm25"), POOL, 5)
        assert result["top5"]["t"][lang] == [h.code for h in live], lang


def test_parse_ad_searches_the_kept_text(fixture_engine, fixtures):
    engine, _ = fixture_engine
    ad = (fixtures / "ads/sv1_utvecklare.txt").read_text()
    a = run(SearchRequest(text=ad, parse_ad=True), engine)
    assert a.passages and a.searched_text != ad
    assert "Friskvårdsbidrag" not in a.searched_text  # benefits are set aside
    assert a.searched_text.startswith("Mjukvaruutvecklare Java")  # the title is kept
    assert a.hits


def test_parse_ad_falls_back_to_the_whole_text(fixture_engine):
    engine, _ = fixture_engine
    ad = "Om oss\nVi är ett bolag.\n\nVi erbjuder\n- Friskvårdsbidrag"
    a = run(SearchRequest(text=ad, parse_ad=True), engine)
    assert a.searched_text == ad and a.passages


def test_without_parse_ad_there_are_no_passages(fixture_engine):
    engine, _ = fixture_engine
    assert run(SearchRequest(text="mjukvaruutvecklare"), engine).passages is None
