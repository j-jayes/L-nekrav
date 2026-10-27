"""Building the occupation map from the vector cache (007 T005, research R1, R3, R4)."""

import hashlib

import numpy as np
import pytest

from lonekrav.core.chunks import chunk_profile
from lonekrav.core.embeddings import FakeEmbedder, cache_file, encode_documents_cached
from lonekrav.core.occupation_map import POOL_KINDS, load_map, load_similarity
from lonekrav.core.profiles import build_profiles
from lonekrav.etl.occupation_map import build_map


@pytest.fixture
def cached(inputs, tmp_path):
    """The fixture profiles, and a vector cache for every chunk text, as `index` writes it."""
    profiles = build_profiles(inputs)
    emb = FakeEmbedder()
    texts = [c.text for p in profiles.values() for c in chunk_profile(p)]
    encode_documents_cached(emb, texts, tmp_path)
    return profiles, cache_file(emb.name, emb.identity, tmp_path), emb.identity


GROUPS = {"2": {"sv": "Yrken med krav på fördjupad högskolekompetens",
                "en": "Occupations requiring advanced level of higher education"}}


def first_two(X):  # a stand-in for UMAP: deterministic, no numba
    return X[:, :2]


def test_writes_both_artefacts_with_their_provenance(cached, tmp_path):
    profiles, cache, identity = cached
    m = build_map(profiles, cache, identity, "2026-10-27", GROUPS, reduce=first_two, out_dir=tmp_path)
    again = load_map(tmp_path / "occupation_map.json")
    assert again == m
    assert m.model == identity and m.chunk_kinds == list(POOL_KINDS) and m.ilo_excluded
    assert m.built_on == "2026-10-27" and len(m.pair_quantiles) == 101 and m.major_groups == GROUPS
    assert [p.code for p in m.points] == sorted(profiles)
    assert all(0 <= p.x <= 1 and 0 <= p.y <= 1 for p in m.points)
    assert all(p.major_group == p.code[0] for p in m.points)
    sim = load_similarity(tmp_path / "occupation_similarity.parquet")
    n = len(profiles)
    assert len(sim) == n * (n - 1) // 2 and all(a < b for a, b in sim)


def test_the_chunk_set_hash_names_exactly_the_chunks_pooled(cached, tmp_path):
    profiles, cache, identity = cached
    m = build_map(profiles, cache, identity, "2026-10-27", GROUPS, reduce=first_two, out_dir=tmp_path)
    ids = sorted(c.chunk_id for p in profiles.values() for c in chunk_profile(p)
                 if c.kind in POOL_KINDS and not c.ilo)
    assert m.chunk_set_sha256 == hashlib.sha256("\n".join(ids).encode()).hexdigest()


def test_neighbours_agree_with_the_pair_table(cached, tmp_path):
    profiles, cache, identity = cached
    m = build_map(profiles, cache, identity, "2026-10-27", GROUPS, reduce=first_two, out_dir=tmp_path)
    sim = load_similarity(tmp_path / "occupation_similarity.parquet")
    for p in m.points:
        others = sorted(((sim[tuple(sorted((p.code, o)))], o) for o in profiles if o != p.code), reverse=True)
        assert [n.cosine for n in p.neighbours] == [round(c, 3) for c, _ in others[:len(p.neighbours)]]


def test_a_missing_cached_vector_fails_loudly(cached, tmp_path):
    profiles, cache, identity = cached
    with np.load(cache) as z:
        np.savez(tmp_path / "partial.npz", keys=z["keys"][:3], vectors=z["vectors"][:3])
    with pytest.raises(KeyError, match="lonekrav-etl index"):
        build_map(profiles, tmp_path / "partial.npz", identity, "2026-10-27", GROUPS, reduce=first_two, out_dir=tmp_path)


def test_umap_layout_is_reproducible(cached, tmp_path):
    pytest.importorskip("umap")
    profiles, cache, identity = cached
    one = build_map(profiles, cache, identity, "2026-10-27", GROUPS, out_dir=tmp_path / "a")
    two = build_map(profiles, cache, identity, "2026-10-27", GROUPS, out_dir=tmp_path / "b")
    assert [(p.x, p.y) for p in one.points] == [(p.x, p.y) for p in two.points]
    assert one.umap["n_neighbors"] <= len(profiles) - 1
