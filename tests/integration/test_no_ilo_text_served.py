"""ILO ISCO-08 text ranks but is never served (Feature 004; ILO reserves reproduction rights)."""

from fastapi.testclient import TestClient

from lonekrav.core import profiles as prof
from lonekrav.etl import ilo


def test_search_never_shows_ilo_text(inputs, fixtures, tmp_path, build_index, salaries):
    from lonekrav.app import create_app
    from lonekrav.core.search import SearchEngine

    base = prof.build_profiles(inputs)
    groups = ilo.parse(fixtures / "ilo/isco08_en.xlsx")
    with_ilo = prof.attach_ilo(base, groups, {c: p.isco_codes for c, p in base.items()})
    ilo_texts = [d.text for p in with_ilo.values() for d in p.descriptions
                 if d.source.source == "ilo_isco08"]
    assert ilo_texts, "the fixture ILO file should give some text"
    store, embedders, titles, _ = build_index(with_ilo, tmp_path / "ilo.db")
    engine = SearchEngine(store=store, embedders=embedders, titles=titles)
    with TestClient(create_app(engine=engine, profiles=base, salaries=salaries)) as client:
        for query in ilo_texts[:5]:  # the ILO text itself is the strongest match for its chunk
            body = client.post("/api/v1/search", json={"text": query[:2000], "mode": "fast"}).json()
            shown = [h["matched_chunk"]["text"] for h in body["hits"]]
            assert body["hits"] and not any(s in t or t in s for s in shown for t in ilo_texts)
    store.client.close()
