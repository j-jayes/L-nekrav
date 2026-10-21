"""Cached, atomic downloads. A failed or invalid download never replaces a good cached file."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from collections.abc import Callable
from pathlib import Path

import httpx
from pydantic import BaseModel

USER_AGENT = "lonekrav/0.1 (+https://github.com/j-jayes/L-nekrav)"


class FetchError(RuntimeError):
    """A download failed. The message names the source and the URL."""


class Meta(BaseModel):
    url: str
    params: dict[str, str] = {}
    fetched_at: dt.datetime
    sha256: str


def meta_path(dest: Path) -> Path:
    return dest.with_name(dest.name + ".meta.json")


def read_meta(dest: Path) -> Meta:
    return Meta.model_validate_json(meta_path(dest).read_text())


def cached_get(
    source: str,
    url: str,
    dest: Path,
    *,
    params: dict[str, str] | None = None,
    client: httpx.Client | None = None,
    force: bool = False,
    validate: Callable[[bytes], object] | None = None,
) -> Path:
    """Download `url` to `dest` unless it is cached, writing `<dest>.meta.json` beside it."""
    if dest.exists() and meta_path(dest).exists() and not force:
        return dest
    own = client is None
    client = client or httpx.Client(timeout=120, follow_redirects=True,
                                    headers={"User-Agent": USER_AGENT})
    try:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.content
        if validate:
            validate(data)
    except Exception as e:
        raise FetchError(f"{source}: download failed for {url}: {e}") from e
    finally:
        if own:
            client.close()
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(dest)
    meta = Meta(url=url, params=params or {}, fetched_at=dt.datetime.now(dt.UTC),
                sha256=hashlib.sha256(data).hexdigest())
    meta_path(dest).write_text(json.dumps(meta.model_dump(mode="json"), indent=1))
    return dest
