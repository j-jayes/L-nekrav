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


INFLECTION = 3  # trailing word characters still counted as the same word (FR-018a)


def _pattern(phrase: str) -> re.Pattern:
    return re.compile(rf"(?<!\w){re.escape(phrase.casefold().strip())}\w{{0,{INFLECTION}}}(?!\w)")


def phrase_in(phrase: str, text: str) -> bool:
    """Does `phrase` occur in `text` as whole words, allowing a short inflectional ending?
    "business manager" is in "Business managers are…"; "manage" is not in "management"."""
    return bool(_pattern(phrase).search(text.casefold()))


class _Leaks:
    """Does a phrase survive in the indexed text of its answer once its own labels are held out?
    Mirrors `chunk_profile`: titles and descriptions always stay, synonyms go by whole label."""

    def __init__(self, profiles: dict[str, OccupationProfile]):
        self.fixed = {c: " ".join([p.title_sv, p.title_en, *(d.text for d in p.descriptions)])
                      .casefold() for c, p in profiles.items()}
        self.labels = {c: [s.label.casefold().strip() for s in p.synonyms]
                       for c, p in profiles.items()}

    def __call__(self, phrase: str, codes: list[str], held: set[str]) -> bool:
        pat = _pattern(phrase)
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
        for m in name.esco:  # preferred label first, then ESCO's other English labels
            occ = inputs.esco.get(m.uri)
            if not occ or m.match_type not in ("exact", "close"):
                continue
            for label in filter(None, (occ.label.get("en"), *occ.alt.get("en", []))):
                if (owners_en.get(label.casefold(), set()) <= set(expected)
                        and not leaks(label, expected, own(name, label))):
                    text_en = label
                    break
            if text_en:
                break
        queries.append(BenchmarkQuery(id=f"gen-{jt_code}", origin="generated", type="title",
                                      text_sv=name.label, text_en=text_en,
                                      expected_codes=expected))
        held |= {name.label.casefold().strip(), *(a.casefold().strip() for a in name.alt_labels)}
        if text_en:
            held.add(text_en.casefold().strip())
    return queries, held


def evaluate(queries: list[BenchmarkQuery], engine, methods: tuple[str, ...],
             depth: int = 10) -> dict:
    """Rank every query in each language through the live search path (FR-017); return metrics,
    per-query ranks and fused top-5 lists.

    "fused" fuses every method at the full-mode pool; with three methods, "fused_fast" fuses
    kblab and bm25 at the fast-mode pool (`search.MODES`), from the same chunk fetch."""
    from lonekrav.core.benchmark import first_rank, mrr, recall_at
    from lonekrav.core.search import FAST_POOL, MODES, POOL, title_parts

    texts = {lang: [(q, getattr(q, f"text_{lang}")) for q in queries if getattr(q, f"text_{lang}")]
             for lang in ("en", "sv")}
    ranks: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    top5: dict = defaultdict(dict)
    rows = {q.id: {"id": q.id, "origin": q.origin, "paired": bool(q.text_en),
                   "form": "slash" if "/" in q.text_sv else "single", "ranks": {}}
            for q in queries}
    fast_methods = MODES["fast"] if len(methods) > 2 and set(MODES["fast"]) <= set(methods) else None
    for lang, items in texts.items():
        for q, text in items:
            hits = engine.chunk_hits(title_parts(text) or [text], methods, POOL)
            per = engine.ranking(hits, POOL)
            ranked = {m: [c for c, _ in per[m][:depth]] for m in methods}
            ranked["fused"] = [h.code for h in engine.fused(per, depth)]
            if fast_methods:
                fast = engine.ranking({m: hits[m] for m in fast_methods}, FAST_POOL)
                ranked["fused_fast"] = [h.code for h in engine.fused(fast, depth)]
            rows[q.id]["ranks"][lang] = {}
            paired = bool(q.text_en)
            origin = q.origin if paired else f"{q.origin}_sv_only"
            for m, codes in ranked.items():
                r = first_rank(codes, set(q.expected_codes))
                rows[q.id]["ranks"][lang][m] = r
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
            "handwritten_top5_overlap_ge3": overlap / len(hw) if hw else None,
            "diagnosis": diagnose(list(rows.values())), "top5": top5,
            "per_query": list(rows.values())}


def diagnose(rows: list[dict], method: str = "fused") -> dict:
    """Split the English–Swedish Recall@5 gap over paired queries by origin and query form.

    The gap is a mean of per-query differences (hit in English − hit in Swedish), so each group's
    share adds up exactly to the whole (FR-018)."""
    paired = [r for r in rows if r["paired"]]

    def hit(r, lang):
        rank = r["ranks"].get(lang, {}).get(method)
        return rank is not None and rank <= 5

    n = len(paired)
    gap = sum(hit(r, "en") - hit(r, "sv") for r in paired) / n if n else None
    groups = defaultdict(list)
    for r in paired:
        groups[(r["origin"], r["form"])].append(r)
    out = []
    for (origin, form), rs in sorted(groups.items()):
        points = sum(hit(r, "en") - hit(r, "sv") for r in rs) / n
        out.append({"origin": origin, "form": form, "n": len(rs),
                    "recall_at_5": {lang: sum(hit(r, lang) for r in rs) / len(rs)
                                    for lang in ("en", "sv")},
                    "gap_points": points, "share_of_gap": points / gap if gap else None})
    return {"method": method, "n_paired": n, "gap": gap, "groups": out}


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
    from lonekrav.core.search import SearchEngine

    embedders = {m: get_embedder(m) for m in methods if m != "bm25"}
    engine = SearchEngine(store=Store(db), embedders=embedders, titles={})
    result = evaluate(queries, engine, tuple(methods))
    result = {
        "run_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "models": {m: f"{SPECS[m].hf_id}@{SPECS[m].revision[:12]}" for m in embedders},
        "n_queries": {"handwritten": sum(q.origin == "handwritten" for q in queries),
                      "generated": sum(q.origin == "generated" for q in queries),
                      "generated_with_english": sum(q.origin == "generated" and bool(q.text_en)
                                                    for q in queries)},
        **{k: v for k, v in result.items() if k not in ("top5", "per_query")},
        "previous": _headline(out / "benchmark_results_001.json"),
    }
    (out / "benchmark_results.json").write_text(json.dumps(result, indent=1) + "\n")
    return result


def _headline(path: Path) -> dict | None:
    """The numbers a run is compared against: the Feature 001 baseline (FR-019)."""
    import json

    if not path.exists():
        return None
    r = json.loads(path.read_text())
    fused = r["metrics"]["fused"]
    return {"source": path.name, "run_at": r["run_at"],
            "fused_recall_at_5": {lang: fused[lang]["all_paired"]["recall_at_5"] for lang in fused},
            "n_paired": fused["en"]["all_paired"]["n"],
            "gap": r["gap_recall_at_5"]["fused"]["all_paired"],
            "handwritten_top5_overlap_ge3": r["handwritten_top5_overlap_ge3"]}


def table(result: dict) -> str:
    rows = ["method   lang  set           R@1    R@5    MRR    n"]
    for m, by_lang in result["metrics"].items():
        for lang, by_o in by_lang.items():
            for o, v in sorted(by_o.items()):
                rows.append(f"{m:<8} {lang:<5} {o:<13} {v['recall_at_1']:.3f}  "
                            f"{v['recall_at_5']:.3f}  {v['mrr']:.3f}  {v['n']}")
    d = result.get("diagnosis")
    if d:
        rows += ["", f"gap diagnosis ({d['method']}, paired n={d['n_paired']}, gap={d['gap']:.3f})",
                 "origin       form    n    R@5 en  R@5 sv  gap pts  share"]
        for g in d["groups"]:
            share = f"{g['share_of_gap']:.2f}" if g["share_of_gap"] is not None else "-"
            rows.append(f"{g['origin']:<12} {g['form']:<7} {g['n']:<4} "
                        f"{g['recall_at_5']['en']:.3f}   {g['recall_at_5']['sv']:.3f}   "
                        f"{g['gap_points']:+.3f}   {share}")
    p = result.get("previous")
    if p:
        f, gap = result["metrics"]["fused"], result["gap_recall_at_5"]["fused"]["all_paired"]
        now = {lang: f[lang]["all_paired"]["recall_at_5"] for lang in ("en", "sv")}
        recall = (f"fused R@5 en {p['fused_recall_at_5']['en']:.3f} -> {now['en']:.3f}; "
                  f"sv {p['fused_recall_at_5']['sv']:.3f} -> {now['sv']:.3f}")
        rest = (f"paired n {p['n_paired']} -> {f['en']['all_paired']['n']}; "
                f"gap {p['gap']:.3f} -> {gap:.3f}; overlap "
                f"{p['handwritten_top5_overlap_ge3']:.3f} -> "
                f"{result['handwritten_top5_overlap_ge3']:.3f}")
        rows += ["", f"vs {p['source']} ({p['run_at']})", recall, rest]
    return "\n".join(rows)


def load_cutoff(path: Path = Path("data/processed/benchmark_results.json")) -> float | None:
    """The low-confidence cut-off chosen by the last benchmark run (FR-017a), if there is one."""
    import json

    return json.loads(path.read_text()).get("low_confidence", {}).get("cutoff") if path.exists() else None
