import shutil

from lonekrav.core.chunks import chunk_profile
from lonekrav.core.embeddings import FakeEmbedder
from lonekrav.core.profiles import build_profiles
from lonekrav.core.search import search
from lonekrav.core.store import Store


def build_index(profiles, db):
    emb = FakeEmbedder(dim=128, name="kblab")
    chunks = [c for p in profiles.values() for c in chunk_profile(p)]
    store = Store(db, dims={"kblab": emb.dim})
    store.create()
    store.insert(chunks, {"kblab": emb.encode_documents([c.text for c in chunks])})
    titles = {c: (p.title_sv, p.title_en) for c, p in profiles.items()}
    return store, {"kblab": emb}, titles, len(chunks)


def test_bm25_finds_swedish_title(inputs, tmp_path):
    store, _embs, titles, _ = build_index(build_profiles(inputs), tmp_path / "t.db")
    hits = search("mjukvaruutvecklare", methods=("bm25",), store=store, titles=titles)
    assert hits[0].code == "2512"
    assert hits[0].title_en == "Software- and system developers"


def test_fused_hit_carries_every_method(inputs, tmp_path):
    store, embs, titles, _ = build_index(build_profiles(inputs), tmp_path / "t.db")
    hits = search("backend developer", methods=("kblab", "bm25"), store=store, embedders=embs,
                  titles=titles)
    assert set(hits[0].scores) == {"kblab", "bm25"}
    assert hits[0].matched_chunk.text
    assert [h.fused_rank for h in hits] == list(range(1, len(hits) + 1))
    scores = [h.fused_score for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_rebuild_gives_same_results(inputs, tmp_path):
    profiles = build_profiles(inputs)
    db = tmp_path / "t.db"
    store, embs, titles, n = build_index(profiles, db)
    first = search("organisationsutvecklare", methods=("kblab", "bm25"), store=store,
                   embedders=embs, titles=titles)
    assert store.count() == n
    store.client.close()
    shutil.rmtree(db) if db.is_dir() else db.unlink()
    store, embs, titles, _ = build_index(profiles, db)
    again = search("organisationsutvecklare", methods=("kblab", "bm25"), store=store,
                   embedders=embs, titles=titles)
    assert [h.code for h in again] == [h.code for h in first]
