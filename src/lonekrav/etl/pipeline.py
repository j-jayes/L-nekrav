"""The fetch and build steps: raw downloads -> committed processed files."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from lonekrav.core import market, salary
from lonekrav.core import profiles as prof
from lonekrav.etl import esco, ilo, jobsearch, jobtech, mis2012, scb_files, scb_pxweb
from lonekrav.etl.benchmark import generate_queries

RAW = Path("data/raw")
PROCESSED = Path("data/processed")


def esco_uris(groups: dict[str, jobtech.Group]) -> list[str]:
    return sorted({m.uri for g in groups.values() for n in g.names for m in n.esco
                   if m.match_type in prof.ESCO_MATCHES})


def history_concepts(raw: Path = RAW) -> list[str]:
    """The JobTech occupation groups behind the SCB codes, as the profiles will carry them."""
    groups = jobtech.parse(raw / "jobtech" / "ssyk_level_4.json")
    codes = set(scb_pxweb.occupation_labels(raw / "pxweb" / "TAB5932.json"))
    return sorted({g.concept_id for g in jobtech.expand_merged(groups, codes).values()})


def fetch(only: list[str] | None = None, force: bool = False, raw: Path = RAW) -> None:
    want = set(only or ("scb_files", "scb_pxweb", "jobtech", "ilo", "mis2012", "esco",
                        "jobsearch_history"))
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
    if "jobsearch_history" in want:
        concepts, years = history_concepts(raw), jobsearch.years(dt.date.today())
        print(f"fetch jobsearch_history ({len(concepts)} concepts x {len(years)} years) ...",
              flush=True)
        jobsearch.fetch_history(raw, concepts, years, force=force)


def load_inputs(raw: Path = RAW) -> prof.Inputs:
    labels = scb_pxweb.occupation_labels(raw / "pxweb" / "TAB5932.json")
    groups = jobtech.parse(raw / "jobtech" / "ssyk_level_4.json")
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
        esco=esco.load(raw, esco_uris(groups)),
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
    regional = scb_pxweb.build_regional(raw)
    salary.write_regional(regional, out / "salary_regional.parquet")
    concepts = sorted({p.jobtech_concept_id for p in profiles.values() if p.jobtech_concept_id})
    history = jobsearch.build_history(raw, concepts, jobsearch.years(dt.date.today()))
    market.write_history(history, out / "ad_history.parquet")
    queries, held = generate_queries(inputs, profiles)
    (out / "benchmark_generated.json").write_text(json.dumps(
        [q.model_dump() for q in queries], ensure_ascii=False, indent=1) + "\n")
    (out / "benchmark_holdout.json").write_text(json.dumps(
        sorted(held), ensure_ascii=False, indent=1) + "\n")
    print(f"built {len(profiles)} profiles, {len(dists)} distributions, {len(ages)} age rows, "
          f"{len(regional)} regional rows, {len(history)} yearly ad counts, "
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
    from lonekrav.core.embeddings import SPECS, encode_documents_cached, get_embedder
    from lonekrav.core.store import Store
    from lonekrav.core.text import profile_vocab

    held = holdout_titles(out)
    profiles = prof.load_profiles(out / "ssyk_profiles.json")
    vocab = profile_vocab(profiles.values())  # from committed profiles, as at query time
    ilo_groups = ilo.parse(ilo.fetch(raw))  # cached after the first download
    profiles = prof.attach_ilo(profiles, ilo_groups, {c: p.isco_codes for c, p in profiles.items()})
    chunks = [c for p in profiles.values() for c in chunk_profile(p, holdout=held)]
    print(f"index {len(chunks)} chunks from {len(profiles)} profiles ({len(held)} held out)")
    vectors = {}
    for m in models:
        t = time.perf_counter()
        vectors[m] = encode_documents_cached(get_embedder(m), [c.text for c in chunks],
                                             raw / "embeddings")
        print(f"  {m}: {time.perf_counter() - t:.0f} s")
    store = Store(db, dims={m: SPECS[m].dim for m in models}, vocab=vocab)
    store.create()
    store.insert(chunks, vectors)
    print(f"  wrote {store.count()} chunks to {store.uri}")
