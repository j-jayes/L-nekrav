"""The fetch and build steps: raw downloads -> committed processed files."""

from __future__ import annotations

import json
from pathlib import Path

from lonekrav.core import profiles as prof
from lonekrav.core import salary
from lonekrav.etl import esco, ilo, jobtech, mis2012, scb_files, scb_pxweb
from lonekrav.etl.benchmark import generate_queries

RAW = Path("data/raw")
PROCESSED = Path("data/processed")


def esco_uris(groups: dict[str, jobtech.Group]) -> list[str]:
    return sorted({m.uri for g in groups.values() for n in g.names for m in n.esco
                   if m.match_type in prof.ESCO_MATCHES})


def fetch(only: list[str] | None = None, force: bool = False, raw: Path = RAW) -> None:
    want = set(only or ("scb_files", "scb_pxweb", "jobtech", "ilo", "mis2012", "esco"))
    steps = [("scb_files", scb_files.fetch), ("scb_pxweb", scb_pxweb.fetch),
             ("jobtech", jobtech.fetch), ("ilo", ilo.fetch), ("mis2012", mis2012.fetch)]
    for name, step in steps:
        if name in want:
            print(f"fetch {name} ...", flush=True)
            step(raw, force=force)
    if "esco" in want:
        uris = esco_uris(jobtech.parse(raw / "jobtech" / "ssyk_level_4.json"))
        print(f"fetch esco ({len(uris)} occupations) ...", flush=True)
        got = esco.fetch(raw, uris, force=force)
        print(f"  esco: {len(got.paths)} cached, {len(got.missing)} no longer in ESCO (skipped)")


def load_inputs(raw: Path = RAW) -> prof.Inputs:
    labels = scb_pxweb.occupation_labels(raw / "pxweb" / "TAB5932.json")
    groups = jobtech.parse(raw / "jobtech" / "ssyk_level_4.json")
    occs = {}
    for uri in esco_uris(groups):
        path = esco.path_for(raw, uri)
        if path.exists():
            occs[uri] = esco.parse(path)
    s = raw / "scb"
    return prof.Inputs(
        salary_labels=labels,
        structure=scb_files.parse_structure(s / scb_files.FILES["structure"]),
        english=scb_files.parse_english(s / scb_files.FILES["english"]),
        title_index=scb_files.parse_title_index(s / scb_files.FILES["title_index"]),
        isco_key=scb_files.parse_isco_key(s / scb_files.FILES["isco_key"]),
        jobtech=groups,
        jobtech_by_scb=jobtech.expand_merged(groups, set(labels)),
        ilo=ilo.parse(raw / "ilo" / "isco08_en.xlsx"),
        esco=occs,
        mis=mis2012.parse(mis2012.load_pages(raw / "mis2012" / "pages.json")),
    )


def build(raw: Path = RAW, out: Path = PROCESSED) -> None:
    inputs = load_inputs(raw)
    profiles = prof.build_profiles(inputs)
    prof.write_profiles(profiles, out / "ssyk_profiles.json")
    prof.write_discrepancies(prof.discrepancies(inputs), out / "discrepancies.csv")
    dists = scb_pxweb.build_distributions(raw)
    ages = scb_pxweb.build_age_bands(raw)
    salary.write_distributions(dists, out / "salary_distributions.parquet")
    salary.write_age_bands(ages, out / "salary_age.parquet")
    queries, held = generate_queries(inputs, profiles)
    (out / "benchmark_generated.json").write_text(json.dumps(
        [q.model_dump() for q in queries], ensure_ascii=False, indent=1) + "\n")
    (out / "benchmark_holdout.json").write_text(json.dumps(
        sorted(held), ensure_ascii=False, indent=1) + "\n")
    print(f"built {len(profiles)} profiles, {len(dists)} distributions, {len(ages)} age rows, "
          f"{len(queries)} generated queries ({sum(bool(q.text_en) for q in queries)} with English)")


def holdout_titles(out: Path = PROCESSED) -> set[str]:
    """Case-folded benchmark query titles to keep out of the index (empty before build)."""
    p = out / "benchmark_holdout.json"
    return set(json.loads(p.read_text())) if p.exists() else set()


def index(models: list[str], db: Path | None = None, out: Path = PROCESSED,
          raw: Path = RAW) -> None:
    """Index the committed profiles plus ILO text (not committed; fetched here if missing)."""
    import time

    from lonekrav.core.chunks import chunk_profile
    from lonekrav.core.embeddings import SPECS, get_embedder
    from lonekrav.core.store import Store

    held = holdout_titles(out)
    profiles = prof.load_profiles(out / "ssyk_profiles.json")
    ilo_groups = ilo.parse(ilo.fetch(raw))  # cached after the first download
    profiles = prof.attach_ilo(profiles, ilo_groups, {c: p.isco_codes for c, p in profiles.items()})
    chunks = [c for p in profiles.values() for c in chunk_profile(p, holdout=held)]
    print(f"index {len(chunks)} chunks from {len(profiles)} profiles ({len(held)} held out)")
    vectors = {}
    for m in models:
        t = time.perf_counter()
        vectors[m] = get_embedder(m).encode_documents([c.text for c in chunks])
        print(f"  {m}: {time.perf_counter() - t:.0f} s")
    store = Store(db, dims={m: SPECS[m].dim for m in models})
    store.create()
    store.insert(chunks, vectors)
    print(f"  wrote {store.count()} chunks to {store.uri}")
