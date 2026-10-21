"""Benchmark set generation (from official JobTech title-to-code links) and the benchmark run."""

from __future__ import annotations

import random
import re
from collections import defaultdict
from pathlib import Path

from lonekrav.core.benchmark import BenchmarkQuery
from lonekrav.core.models import OccupationProfile
from lonekrav.core.profiles import Inputs, attach_ilo

SEED = 2026
HANDWRITTEN = Path(__file__).parents[3] / "tests" / "eval" / "queries_handwritten.yaml"


def _owners(profiles: dict[str, OccupationProfile], lang: str) -> dict[str, set[str]]:
    owners: dict[str, set[str]] = defaultdict(set)
    for code, p in profiles.items():
        for s in p.synonyms:
            if s.lang == lang:
                owners[s.label.casefold().strip()].add(code)
    return owners


class _Leaks:
    """Does a phrase survive in the indexed text of its answer once its own labels are held out?
    Mirrors `chunk_profile`: titles and descriptions always stay, synonyms go by whole label."""

    def __init__(self, profiles: dict[str, OccupationProfile]):
        self.fixed = {c: " ".join([p.title_sv, p.title_en, *(d.text for d in p.descriptions)])
                      .casefold() for c, p in profiles.items()}
        self.labels = {c: [s.label.casefold().strip() for s in p.synonyms]
                       for c, p in profiles.items()}

    def __call__(self, phrase: str, codes: list[str], held: set[str]) -> bool:
        pat = re.compile(rf"(?<!\w){re.escape(phrase.casefold().strip())}(?!\w)")
        return any(pat.search(self.fixed[c])
                   or any(pat.search(lab) for lab in self.labels[c] if lab not in held)
                   for c in codes)


def generate_queries(inputs: Inputs, profiles: dict[str, OccupationProfile],
                     seed: int = SEED) -> tuple[list[BenchmarkQuery], set[str]]:
    """One title query per JobTech group, labelled with its official SSYK code(s).

    Skips official occupation titles, titles that also belong to other occupations, and titles that would still appear in
    the indexed text of their answer after hold-out (in its title, a description, ILO text or a
    longer label), since those test lookup rather than retrieval. Returns the queries and the
    case-folded titles to hold out of the index.
    """
    rng = random.Random(seed)
    official = {p.title_sv.casefold() for p in profiles.values()}
    leaks = _Leaks(attach_ilo(profiles, inputs.ilo, inputs.isco_key))
    owners_sv, owners_en = _owners(profiles, "sv"), _owners(profiles, "en")
    queries, held = [], set()
    for jt_code, group in sorted(inputs.jobtech.items()):
        expected = sorted(c for c, g in inputs.jobtech_by_scb.items()
                          if g.concept_id == group.concept_id and c in profiles)

        def own(n, *extra):
            return {n.label.casefold().strip(), *(a.casefold().strip() for a in n.alt_labels),
                    *(e.casefold().strip() for e in extra)}

        candidates = [n for n in group.names
                      if (k := n.label.casefold().strip()) not in official
                      and owners_sv.get(k, set()) <= set(expected)
                      and not leaks(n.label, expected, own(n))]
        if not expected or not candidates:
            continue
        name = rng.choice(candidates)
        text_en = None
        for m in name.esco:
            occ = inputs.esco.get(m.uri)
            label = occ.label.get("en") if occ and m.match_type in ("exact", "close") else None
            if (label and owners_en.get(label.casefold(), set()) <= set(expected)
                    and not leaks(label, expected, own(name, label))):
                text_en = label
                break
        queries.append(BenchmarkQuery(id=f"gen-{jt_code}", origin="generated", type="title",
                                      text_sv=name.label, text_en=text_en,
                                      expected_codes=expected))
        held |= {name.label.casefold().strip(), *(a.casefold().strip() for a in name.alt_labels)}
        if text_en:
            held.add(text_en.casefold().strip())
    return queries, held


def evaluate(queries: list[BenchmarkQuery], store, embedders: dict, methods: tuple[str, ...],
             depth: int = 10) -> dict:
    """Rank every query in each language; return metrics and per-query fused top-5 lists."""
    from lonekrav.core.benchmark import first_rank, mrr, recall_at
    from lonekrav.core.search import POOL, ChunkHit, fuse, reduce_to_codes

    texts = {lang: [(q, getattr(q, f"text_{lang}")) for q in queries if getattr(q, f"text_{lang}")]
             for lang in ("en", "sv")}
    ranks: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    top5: dict = defaultdict(dict)
    for lang, items in texts.items():
        vecs = {m: embedders[m].encode_queries([t for _, t in items]) for m in methods if m != "bm25"}
        for i, (q, text) in enumerate(items):
            per = {}
            for m in methods:
                raw = (store.search_bm25(text, POOL) if m == "bm25"
                       else store.search_dense(m, vecs[m][i], POOL))
                per[m] = reduce_to_codes([ChunkHit(**h) for h in raw])
            ranked = {m: [c for c, _ in per[m][:depth]] for m in methods}
            ranked["fused"] = [h.code for h in fuse(per, k=depth)]
            paired = bool(q.text_en)
            origin = q.origin if paired else f"{q.origin}_sv_only"
            for m, codes in ranked.items():
                r = first_rank(codes, set(q.expected_codes))
                ranks[m][lang][origin].append(r)
                if paired:
                    ranks[m][lang]["all_paired"].append(r)
            top5[q.id][lang] = ranked["fused"][:5]
    metrics = {m: {lang: {o: {"recall_at_1": recall_at(v, 1), "recall_at_5": recall_at(v, 5),
                              "mrr": mrr(v), "n": len(v)} for o, v in by_o.items()}
                   for lang, by_o in by_lang.items()} for m, by_lang in ranks.items()}
    gap = {m: {o: metrics[m]["en"][o]["recall_at_5"] - metrics[m]["sv"][o]["recall_at_5"]
               for o in metrics[m]["en"] if o in metrics[m]["sv"]} for m in metrics}
    hw = [q for q in queries if q.origin == "handwritten"]
    overlap = sum(len(set(top5[q.id]["en"]) & set(top5[q.id]["sv"])) >= 3 for q in hw)
    return {"metrics": metrics, "gap_recall_at_5": gap,
            "handwritten_top5_overlap_ge3": overlap / len(hw) if hw else None, "top5": top5}


def run(db=None, out=None, methods=("kblab", "harrier", "bm25")) -> dict:
    import datetime as dt
    import json

    from lonekrav.core.benchmark import load_handwritten
    from lonekrav.core.embeddings import SPECS, get_embedder
    from lonekrav.core.store import Store

    out = out or Path("data/processed")
    queries = load_handwritten(HANDWRITTEN) + [
        BenchmarkQuery.model_validate(q)
        for q in json.loads((out / "benchmark_generated.json").read_text())]
    embedders = {m: get_embedder(m) for m in methods if m != "bm25"}
    result = evaluate(queries, Store(db), embedders, tuple(methods))
    result = {
        "run_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "models": {m: f"{SPECS[m].hf_id}@{SPECS[m].revision[:12]}" for m in embedders},
        "n_queries": {"handwritten": sum(q.origin == "handwritten" for q in queries),
                      "generated": sum(q.origin == "generated" for q in queries),
                      "generated_with_english": sum(q.origin == "generated" and bool(q.text_en)
                                                    for q in queries)},
        **{k: v for k, v in result.items() if k != "top5"},
    }
    (out / "benchmark_results.json").write_text(json.dumps(result, indent=1) + "\n")
    return result


def table(result: dict) -> str:
    rows = ["method   lang  set           R@1    R@5    MRR    n"]
    for m, by_lang in result["metrics"].items():
        for lang, by_o in by_lang.items():
            for o, v in sorted(by_o.items()):
                rows.append(f"{m:<8} {lang:<5} {o:<13} {v['recall_at_1']:.3f}  "
                            f"{v['recall_at_5']:.3f}  {v['mrr']:.3f}  {v['n']}")
    return "\n".join(rows)
