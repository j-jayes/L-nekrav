from pathlib import Path

import pytest

from lonekrav.core.chunks import chunk_profile
from lonekrav.core.embeddings import FakeEmbedder
from lonekrav.core.profiles import Inputs, build_profiles
from lonekrav.core.store import Store
from lonekrav.core.text import profile_vocab
from lonekrav.etl import esco, ilo, jobtech, mis2012, scb_files, scb_pxweb

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def _release_milvus_lite(tmp_path_factory):
    """Stop the Milvus Lite server each test's temporary index started.

    Milvus Lite runs one in-process gRPC server per database path until the process exits. With
    hundreds of them alive, a test that starts a subprocess (test_openmp_order, test_index_search)
    can crash in gRPC's fork handler. Only paths under pytest's temporary base are released, so
    the benchmark's module-scoped index on data/index keeps running."""
    yield
    import sys

    if "milvus_lite.server_manager" not in sys.modules:
        return
    from milvus_lite.server_manager import server_manager_instance as manager

    base = str(tmp_path_factory.getbasetemp())
    for path in [p for p in manager._servers if p.startswith(base)]:  # no public listing
        manager.release_server(path)


@pytest.fixture
def fixtures() -> Path:
    return FIXTURES


@pytest.fixture
def inputs(fixtures) -> Inputs:
    f = fixtures
    labels = scb_pxweb.occupation_labels(f / "pxweb/TAB5932.json")
    groups = jobtech.parse(f / "jobtech/ssyk_level_4.json")
    return Inputs(
        salary_labels=labels,
        structure=scb_files.parse_structure(f / "scb/ssyk-2012-koder.xlsx"),
        english=scb_files.parse_english(f / "scb/structur_english_ssyk2012_1_4.xlsx"),
        title_index=scb_files.parse_title_index(f / "scb/ssyk_index_webb_2026.xlsx"),
        isco_key=scb_files.parse_isco_key(f / "scb/webb_nyckel_ssyk2012_isco-08_20160905.xlsx"),
        jobtech=groups,
        jobtech_by_scb=jobtech.expand_merged(groups, set(labels)),
        ilo=ilo.parse(f / "ilo/isco08_en.xlsx"),
        esco={o.uri: o for o in map(esco.parse, sorted((f / "esco").glob("*.json")))},
        mis=mis2012.parse(mis2012.load_pages(f / "mis2012/pages.json")),
    )


def _build_index(profiles, db):
    emb = FakeEmbedder(dim=128, name="kblab")
    chunks = [c for p in profiles.values() for c in chunk_profile(p)]
    store = Store(db, dims={"kblab": emb.dim}, vocab=profile_vocab(profiles.values()))
    store.create()
    store.insert(chunks, {"kblab": emb.encode_documents([c.text for c in chunks])})
    titles = {c: (p.title_sv, p.title_en) for c, p in profiles.items()}
    return store, {"kblab": emb}, titles, len(chunks)


@pytest.fixture
def build_index():
    """Index fixture profiles with the FakeEmbedder: (store, embedders, titles, n_chunks)."""
    return _build_index


@pytest.fixture
def fixture_engine(inputs, tmp_path):
    """A SearchEngine over the fixture index, with the FakeEmbedder standing in for KBLab."""
    from lonekrav.core.search import SearchEngine

    profiles = build_profiles(inputs)
    store, embedders, titles, _ = _build_index(profiles, tmp_path / "api.db")
    yield SearchEngine(store=store, embedders=embedders, titles=titles), profiles
    store.client.close()


@pytest.fixture
def api_client(fixture_engine, salaries):
    from fastapi.testclient import TestClient

    from lonekrav.app import create_app

    engine, profiles = fixture_engine
    with TestClient(create_app(engine=engine, profiles=profiles, salaries=salaries),
                    raise_server_exceptions=False) as client:
        yield client


@pytest.fixture
def salaries(fixtures):
    """Fixture SCB tables parsed as the build does: (distributions, age bands)."""
    import datetime as dt

    t = dt.datetime(2026, 10, 20, 12, tzinfo=dt.UTC)
    px = fixtures / "pxweb"
    return (scb_pxweb.parse_distributions(px / "TAB5932.json", "TAB5932", t),
            scb_pxweb.parse_age_bands(px / "TAB5844.json", "TAB5844", t))
