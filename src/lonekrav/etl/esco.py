"""ESCO occupations (European Commission), English and Swedish labels and descriptions."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import httpx
from pydantic import BaseModel

from lonekrav.etl.http import USER_AGENT, FetchError, cached_get

URL = "https://ec.europa.eu/esco/api/resource/occupation"
LANGS = ("en", "sv")


class Occupation(BaseModel):
    uri: str
    label: dict[str, str]
    alt: dict[str, list[str]]
    description: dict[str, str]


def path_for(raw: Path, uri: str) -> Path:
    return raw / "esco" / (hashlib.sha1(uri.encode()).hexdigest()[:16] + ".json")


class FetchResult(BaseModel):
    paths: list[Path]
    missing: list[str]  # URIs JobTech links to that ESCO cannot serve (see _unservable)


def _unservable(e: FetchError) -> bool:
    """404 (removed from ESCO) or a 500 carrying ESCO's own error body (a data defect for that
    one occupation, seen live as CognizoneException). Network errors and 503s are not."""
    cause = e.__cause__
    if not isinstance(cause, httpx.HTTPStatusError):
        return False
    r = cause.response
    if r.status_code == 404:
        return True
    try:
        return r.status_code == 500 and "logref" in r.json()
    except ValueError:
        return False


def fetch(raw: Path, uris: list[str], force: bool = False, delay: float = 0.1) -> FetchResult:
    """One request per URI (the API returns every language at once), politely spaced.

    Occupations ESCO cannot serve are recorded in `esco/missing.json` and skipped. Any other
    failure stops the fetch. The skip list is saved even when the fetch stops.
    """
    known = raw / "esco" / "missing.json"
    missing = set() if force or not known.exists() else set(json.loads(known.read_text()))
    paths = []
    try:
        with httpx.Client(timeout=60, follow_redirects=True,
                          headers={"User-Agent": USER_AGENT}) as c:
            for uri in uris:
                if uri in missing:
                    continue
                dest = path_for(raw, uri)
                fresh = force or not dest.exists()
                try:
                    paths.append(cached_get("esco", URL, dest, client=c, force=force,
                                            params={"uri": uri, "language": "en"},
                                            validate=json.loads))
                except FetchError as e:
                    if not _unservable(e):
                        raise
                    missing.add(uri)
                if fresh:
                    time.sleep(delay)
    finally:
        known.parent.mkdir(parents=True, exist_ok=True)
        known.write_text(json.dumps(sorted(missing), indent=1))
    return FetchResult(paths=paths, missing=sorted(missing))


def load(raw: Path, uris: list[str]) -> dict[str, Occupation]:
    """Parse the cached occupations, leaving out any recorded in `missing.json`: after a forced
    re-fetch a 404 keeps the old file, but the occupation is gone from ESCO."""
    known = raw / "esco" / "missing.json"
    missing = set(json.loads(known.read_text())) if known.exists() else set()
    return {u: parse(p) for u in uris
            if u not in missing and (p := path_for(raw, u)).exists()}


def parse(path: Path) -> Occupation:
    d = json.loads(path.read_text())
    desc = d.get("description") or {}
    return Occupation(
        uri=d["uri"],
        label={k: v for k, v in (d.get("preferredLabel") or {}).items() if k in LANGS},
        alt={k: list(v) for k, v in (d.get("alternativeLabel") or {}).items() if k in LANGS},
        description={k: (desc[k] or {}).get("literal", "").strip() for k in LANGS if k in desc},
    )
