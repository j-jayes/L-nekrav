"""JobTech Taxonomy: SSYK level-4 definitions, occupation-names and their ESCO matches."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from lonekrav.etl.http import cached_get

URL = "https://taxonomy.api.jobtechdev.se/v1/taxonomy/graphql"
MATCHES = ("exact", "close", "broad", "narrow")
_ESCO = "{ esco_uri preferred_label }"
QUERY = (
    '{ concepts(type:"ssyk-level-4") { id ssyk_code_2012 preferred_label definition '
    'narrower(type:"occupation-name") { id preferred_label alternative_labels '
    + " ".join(f'{m}_match(type:"esco-occupation") {_ESCO}' for m in MATCHES)
    + " } } }"
)


class EscoMatch(BaseModel):
    uri: str
    label: str
    match_type: str


class OccupationName(BaseModel):
    id: str
    label: str
    alt_labels: list[str]
    esco: list[EscoMatch]


class Group(BaseModel):
    concept_id: str
    code: str
    label: str
    definition: str
    names: list[OccupationName]
    shared_with: list[str] = []


def _validate(data: bytes) -> None:
    body = json.loads(data)
    if "data" not in body or not body["data"].get("concepts"):
        raise ValueError(f"unexpected GraphQL response: {str(body)[:200]}")


def fetch(raw: Path, force: bool = False) -> Path:
    return cached_get("jobtech", URL, raw / "jobtech" / "ssyk_level_4.json",
                      params={"query": QUERY}, force=force, validate=_validate)


def parse(path: Path) -> dict[str, Group]:
    groups = {}
    for c in json.loads(path.read_text())["data"]["concepts"]:
        names = [
            OccupationName(
                id=n["id"], label=n["preferred_label"], alt_labels=n.get("alternative_labels") or [],
                esco=[EscoMatch(uri=m["esco_uri"], label=m["preferred_label"], match_type=t)
                      for t in MATCHES for m in n.get(f"{t}_match") or []],
            )
            for n in c.get("narrower") or []
        ]
        groups[c["ssyk_code_2012"]] = Group(
            concept_id=c["id"], code=c["ssyk_code_2012"], label=c["preferred_label"],
            definition=(c.get("definition") or "").strip(), names=names,
        )
    return groups


def expand_merged(groups: dict[str, Group], scb_codes: set[str]) -> dict[str, Group]:
    """Key groups by SCB code. JobTech merges manager levels (1210 for 1211 and 1212):
    a JobTech code not used by SCB is attached to every SCB code in the same 3-digit group."""
    out = {c: g for c, g in groups.items() if c in scb_codes}
    for c, g in groups.items():
        if c in scb_codes:
            continue
        levels = sorted(s for s in scb_codes if s[:3] == c[:3] and s not in groups)
        for s in levels:
            out[s] = g.model_copy(update={"shared_with": levels})
    return out
