"""Assemble one OccupationProfile per SSYK 2012 code from the parsed official sources.

Precedence: SCB first, then JobTech, ILO and ESCO. Every text and label keeps its source.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from lonekrav.core.legal_flags import flags_for
from lonekrav.core.models import OccupationProfile, SourceRef, Synonym, Text, dedupe_synonyms

DEFAULT = Path("data/processed/ssyk_profiles.json")
SCB_FILES = "https://www.scb.se/contentassets/0c0089cc085a45d49c1dc83923ad933a/"
REFS = {
    "scb_structure": SourceRef(source="scb_structure", ref="ssyk-2012-koder.xlsx",
                               url=SCB_FILES + "ssyk-2012-koder.xlsx"),
    "scb_pxweb": SourceRef(source="scb_pxweb", ref="TAB5932",
                           url="https://statistikdatabasen.scb.se/api/v2/tables/TAB5932"),
    "scb_english": SourceRef(source="scb_english", ref="structur_english_ssyk2012_1_4.xlsx",
                             url=SCB_FILES + "structur_english_ssyk2012_1_4.xlsx"),
    "scb_title_index": SourceRef(source="scb_title_index", ref="ssyk_index_webb_2026.xlsx",
                                 url=SCB_FILES + "ssyk_index_webb_2026.xlsx"),
    "scb_isco_key": SourceRef(source="scb_isco_key",
                              ref="webb_nyckel_ssyk2012_isco-08_20160905.xlsx",
                              url=SCB_FILES + "webb_nyckel_ssyk2012_isco-08_20160905.xlsx"),
    "scb_mis2012": SourceRef(source="scb_mis2012", ref="SSYK 2012 (MIS 2012:1)",
                             url="https://www.scb.se/contentassets/c9d055b6f2114b62bd23c33602b56da5/"
                                 "ov9999_2012a01_br_x70br1201.pdf"),
    "jobtech": SourceRef(source="jobtech", ref="taxonomy ssyk-level-4",
                         url="https://taxonomy.api.jobtechdev.se/v1/taxonomy/graphql"),
    "ilo_isco08": SourceRef(source="ilo_isco08", ref="ISCO-08 EN Structure and definitions",
                            url="https://www.ilo.org/ilostat-files/ISCO/newdocs-08-2021/ISCO-08/"
                                "ISCO-08%20EN%20Structure%20and%20definitions.xlsx"),
}
ESCO_MATCHES = {"exact", "close", "narrow"}  # broad ESCO concepts can span other SSYK codes


@dataclass
class Inputs:
    salary_labels: dict[str, str]
    structure: dict[str, str]
    english: dict[str, str]
    title_index: dict[str, list[str]]
    isco_key: dict[str, list[str]]
    jobtech: dict  # JobTech code -> group, as JobTech publishes it
    jobtech_by_scb: dict  # SCB code -> group, merged manager codes expanded (etl.jobtech)
    ilo: dict  # ISCO code -> ILO unit group
    esco: dict  # URI -> ESCO occupation
    mis: dict[str, str]


def _esco_ref(uri: str) -> SourceRef:
    return SourceRef(source="esco", ref=uri, url=uri)


def _profile(code: str, inp: Inputs, isco_owners: dict[str, list[str]]) -> OccupationProfile:
    jt = inp.jobtech_by_scb.get(code)
    shared = bool(jt and jt.shared_with)
    isco = inp.isco_key.get(code) or []
    ilo_groups = [inp.ilo[i] for i in isco if i in inp.ilo]
    title_en = inp.english.get(code) or (ilo_groups[0].title if ilo_groups else "")
    sources = [REFS["scb_structure"] if code in inp.structure else REFS["scb_pxweb"]]

    descriptions: list[Text] = []
    if jt and jt.definition and not shared:
        descriptions.append(Text(lang="sv", kind="definition", text=jt.definition,
                                 source=REFS["jobtech"]))
    elif code in inp.mis:
        descriptions.append(Text(lang="sv", kind="definition", text=inp.mis[code],
                                 source=REFS["scb_mis2012"]))
        sources.append(REFS["scb_mis2012"])
        if jt and jt.definition:
            descriptions.append(Text(lang="sv", kind="definition", text=jt.definition,
                                     source=REFS["jobtech"], shared_with=jt.shared_with))
    for g in ilo_groups:
        if g.definition:
            descriptions.append(Text(lang="en", kind="definition", text=g.definition,
                                     source=REFS["ilo_isco08"], isco_code=g.code))
        if g.tasks:
            descriptions.append(Text(lang="en", kind="tasks", text=g.tasks,
                                     source=REFS["ilo_isco08"], isco_code=g.code))
    if ilo_groups:
        sources.append(REFS["ilo_isco08"])
    if code in inp.english:
        sources.append(REFS["scb_english"])
    if jt:
        sources.append(REFS["jobtech"])

    synonyms = [Synonym(lang="sv", label=t, source=REFS["scb_title_index"])
                for t in inp.title_index.get(code, [])]
    esco_seen = []
    for n in jt.names if jt else []:
        synonyms.append(Synonym(lang="sv", label=n.label, source=REFS["jobtech"], jobtech_id=n.id))
        synonyms += [Synonym(lang="sv", label=a, source=REFS["jobtech"], jobtech_id=n.id)
                     for a in n.alt_labels]
        for m in n.esco:
            occ = inp.esco.get(m.uri)
            if m.match_type not in ESCO_MATCHES or occ is None:
                continue
            esco_seen.append(occ)
            for lang in ("en", "sv"):
                labels = [occ.label.get(lang)] + occ.alt.get(lang, [])
                synonyms += [Synonym(lang=lang, label=lab, source=_esco_ref(occ.uri),
                                     esco_uri=occ.uri, match_type=m.match_type)
                             for lab in labels if lab]
    for g in ilo_groups:
        if isco_owners.get(g.code) == [code]:  # unambiguous: this ISCO group maps only here
            synonyms += [Synonym(lang="en", label=t, source=REFS["ilo_isco08"]) for t in g.included]
    for occ in {o.uri: o for o in esco_seen}.values():
        for lang, text in occ.description.items():
            if text:
                descriptions.append(Text(lang=lang, kind="definition", text=text,
                                         source=_esco_ref(occ.uri)))
    if esco_seen:
        sources += [_esco_ref(u) for u in sorted({o.uri for o in esco_seen})]
    if code in inp.title_index:
        sources.append(REFS["scb_title_index"])
    if isco:
        sources.append(REFS["scb_isco_key"])

    return OccupationProfile(
        code=code,
        title_sv=inp.structure.get(code) or inp.salary_labels[code],
        title_en=title_en,
        isco_codes=isco,
        jobtech_concept_id=jt.concept_id if jt else None,
        jobtech_shared=shared,
        descriptions=descriptions,
        synonyms=dedupe_synonyms(synonyms),
        legal_flags=flags_for(code),
        sources=sources,
    )


def build_profiles(inp: Inputs) -> dict[str, OccupationProfile]:
    owners: dict[str, list[str]] = defaultdict(list)
    for code in sorted(inp.salary_labels):
        for i in inp.isco_key.get(code, []):
            owners[i].append(code)
    return {c: _profile(c, inp, owners) for c in sorted(inp.salary_labels)}


def discrepancies(inp: Inputs) -> list[dict]:
    by_scb = inp.jobtech_by_scb
    rows = []
    for code in sorted(inp.salary_labels):
        jt = by_scb.get(code)
        rows.append({
            "code": code,
            "in_structure": code in inp.structure,
            "in_english": code in inp.english,
            "in_salary_table": True,
            "in_isco_key": code in inp.isco_key,
            "in_title_index": code in inp.title_index,
            "in_jobtech": code in inp.jobtech,
            "jobtech_code": jt.code if jt and jt.code != code else "",
            "note": "",
        })
    return rows


def write_profiles(profiles: dict[str, OccupationProfile], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [p.model_dump(mode="json") for _, p in sorted(profiles.items())]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")


def write_discrepancies(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def load_profiles(path: Path = DEFAULT) -> dict[str, OccupationProfile]:
    return {d["code"]: OccupationProfile.model_validate(d) for d in json.loads(path.read_text())}
