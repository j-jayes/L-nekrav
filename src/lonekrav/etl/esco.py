"""ESCO occupations (European Commission), English and Swedish labels and descriptions."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import httpx
from pydantic import BaseModel

from lonekrav.etl.http import USER_AGENT, cached_get

URL = "https://ec.europa.eu/esco/api/resource/occupation"
LANGS = ("en", "sv")


class Occupation(BaseModel):
    uri: str
    label: dict[str, str]
    alt: dict[str, list[str]]
    description: dict[str, str]


def path_for(raw: Path, uri: str) -> Path:
    return raw / "esco" / (hashlib.sha1(uri.encode()).hexdigest()[:16] + ".json")


def fetch(raw: Path, uris: list[str], force: bool = False, delay: float = 0.1) -> list[Path]:
    """One request per URI (the API returns every language at once), politely spaced."""
    paths = []
    with httpx.Client(timeout=60, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as c:
        for uri in uris:
            dest = path_for(raw, uri)
            fresh = force or not dest.exists()
            paths.append(cached_get("esco", URL, dest, params={"uri": uri, "language": "en"},
                                    client=c, force=force, validate=json.loads))
            if fresh:
                time.sleep(delay)
    return paths


def parse(path: Path) -> Occupation:
    d = json.loads(path.read_text())
    desc = d.get("description") or {}
    return Occupation(
        uri=d["uri"],
        label={k: v for k, v in (d.get("preferredLabel") or {}).items() if k in LANGS},
        alt={k: list(v) for k, v in (d.get("alternativeLabel") or {}).items() if k in LANGS},
        description={k: (desc[k] or {}).get("literal", "").strip() for k in LANGS if k in desc},
    )
