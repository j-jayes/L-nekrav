import datetime as dt
import json
import shutil

from lonekrav.etl import pipeline

T = dt.datetime(2026, 10, 20, 12, tzinfo=dt.UTC).isoformat()


def raw_from_fixtures(fixtures, raw):
    """Lay the fixtures out as data/raw/ with the file names the fetchers write."""
    layout = {
        "scb": [(f.name, f) for f in (fixtures / "scb").glob("*.xlsx")],
        "pxweb": [(f.name, f) for f in (fixtures / "pxweb").glob("*.json")],
        "jobtech": [("ssyk_level_4.json", fixtures / "jobtech/ssyk_level_4.json")],
        "ilo": [("isco08_en.xlsx", fixtures / "ilo/isco08_en.xlsx")],
        "mis2012": [("pages.json", fixtures / "mis2012/pages.json")],
    }
    for sub, files in layout.items():
        (raw / sub).mkdir(parents=True, exist_ok=True)
        for name, src in files:
            shutil.copy(src, raw / sub / name)
            (raw / sub / f"{name}.meta.json").write_text(
                json.dumps({"url": "u", "fetched_at": T, "sha256": "x"}))
    from lonekrav.etl import esco
    for f in (fixtures / "esco").glob("*.json"):
        uri = json.loads(f.read_text())["uri"]
        dest = esco.path_for(raw, uri)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(f, dest)


def test_build_twice_is_byte_identical_without_llm_key(fixtures, tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_KEY", raising=False)
    raw = tmp_path / "raw"
    raw_from_fixtures(fixtures, raw)
    a, b = tmp_path / "a", tmp_path / "b"
    pipeline.build(raw=raw, out=a)
    pipeline.build(raw=raw, out=b)
    names = sorted(p.name for p in a.iterdir())
    assert "ssyk_profiles.json" in names and "salary_distributions.parquet" in names
    for name in names:
        assert (a / name).read_bytes() == (b / name).read_bytes(), name
