"""The occupation map: one vector per code, exact neighbours, and closeness (007 US1, research R1-R2)."""

import numpy as np
import pytest

from lonekrav.core.chunks import Chunk
from lonekrav.core.occupation_map import (
    HONEST_SIMILAR,
    POOL_KINDS,
    closeness,
    neighbours,
    pair_quantiles,
    percentile,
    pool,
)
from lonekrav.core.search import HONEST_FIT


def chunk(code, kind, text, ilo=False):
    lang = "mixed" if kind == "title" else kind[-2:]
    return Chunk(chunk_id=f"{code}:{kind}:{text}", code=code, kind=kind, lang=lang, text=text, ilo=ilo)


VECTORS = {
    "a-title": [1, 0, 0], "a-desc": [1, 1, 0], "a-syn": [0, 0, 9], "a-ilo": [0, 0, 9],
    "b-title": [1, 0, 0], "b-desc": [0, 1, 0],
    "c-title": [0, 0, 1],
}
CHUNKS = [
    chunk("1111", "title", "a-title"), chunk("1111", "desc_en", "a-desc"),
    chunk("1111", "synonyms_en", "a-syn"), chunk("1111", "desc_en", "a-ilo", ilo=True),
    chunk("2222", "title", "b-title"), chunk("2222", "desc_sv", "b-desc"),
    chunk("3333", "title", "c-title"),
]


def vec(text):
    return np.array(VECTORS[text], dtype=np.float32) / np.linalg.norm(VECTORS[text])


def test_pool_uses_only_title_and_description_chunks_without_ilo():
    codes, X, counts = pool(CHUNKS, vec)
    assert codes == ["1111", "2222", "3333"]
    assert counts == {"1111": 2, "2222": 2, "3333": 1}  # the synonym and ILO chunks are not used
    assert POOL_KINDS == ("title", "desc_sv", "desc_en")
    expected = vec("a-title") + vec("a-desc")
    np.testing.assert_allclose(X[0], expected / np.linalg.norm(expected), rtol=1e-6)
    np.testing.assert_allclose(np.linalg.norm(X, axis=1), 1, rtol=1e-6)


def test_pool_never_reads_an_ilo_chunk():
    seen = []
    pool(CHUNKS, lambda t: seen.append(t) or vec(t))
    assert "a-ilo" not in seen and "a-syn" not in seen


def test_neighbours_are_the_most_similar_codes_without_self():
    codes, X, _ = pool(CHUNKS, vec)
    near = neighbours(codes, X, k=2)
    assert [n.code for n in near["1111"]] == ["2222", "3333"]
    assert near["1111"][0].cosine == pytest.approx(float(X[0] @ X[1]), abs=1e-3)
    assert all(n.code != c for c, ns in near.items() for n in ns)


def test_pair_quantiles_are_101_sorted_values_of_the_pairs():
    S = np.array([[1, .2, .5], [.2, 1, .8], [.5, .8, 1]])
    q = pair_quantiles(S)
    assert len(q) == 101 and q == sorted(q)
    assert (q[0], q[-1]) == (pytest.approx(.2), pytest.approx(.8))


def test_percentile_is_the_share_of_pairs_less_similar():
    q = [i / 100 for i in range(101)]
    assert percentile(0.505, q) == 50
    assert percentile(0.0, q) == 0
    assert percentile(1.0, q) == 100


def test_near_identical_pairs_share_a_description_and_get_no_percentile():
    q = [i / 100 for i in range(101)]
    same = closeness("1311", "1312", 0.9982, q)
    assert same.same_description and same.percentile is None
    apart = closeness("2511", "2512", 0.939, q)
    assert not apart.same_description and apart.percentile == 93


def test_every_answer_says_the_duties_decide():
    duties = HONEST_FIT.split(". ")[0]
    assert HONEST_SIMILAR.startswith(duties)
    assert closeness("2511", "2512", 0.9, [0.0] * 101).honest_fit == HONEST_SIMILAR


# --- the committed artefacts (SC-001, SC-002, FR-005) ---------------------------------------

def test_stored_neighbours_are_the_ten_most_similar_by_the_pair_table():
    from lonekrav.core.occupation_map import load_map, load_similarity

    m, sim = load_map(), load_similarity()
    codes = [p.code for p in m.points]
    for p in m.points:
        ranked = sorted(((sim[tuple(sorted((p.code, o)))], o) for o in codes if o != p.code), reverse=True)
        assert [round(c, 3) for c, _ in ranked[:10]] == [n.cosine for n in p.neighbours]


def test_neighbours_make_sense_for_known_codes():
    from lonekrav.core.occupation_map import load_map

    near = {p.code: [n.code for n in p.neighbours] for p in load_map().points}
    assert {"2512", "2519"} <= set(near["2511"][:3])
    assert {"2239", "2224"} <= set(near["2221"][:5])


def test_the_map_covers_every_profile_and_holds_no_text():
    import json

    from lonekrav.core.occupation_map import MAP, load_map
    from lonekrav.core.profiles import load_profiles

    m = load_map()
    assert [p.code for p in m.points] == sorted(load_profiles())
    assert m.ilo_excluded and len(m.pair_quantiles) == 101
    strings = []

    def walk(v):
        if isinstance(v, str):
            strings.append(v)
        elif isinstance(v, dict):
            [walk(x) for x in v.values()]
        elif isinstance(v, list):
            [walk(x) for x in v]
    data = json.loads(MAP.read_text())
    assert sorted(data.pop("major_groups")) == [str(d) for d in range(10)]  # SCB's group titles (CC0)
    walk(data)
    assert strings and not [s for s in strings if any(ch.isspace() for ch in s)]  # codes and ids, no prose
