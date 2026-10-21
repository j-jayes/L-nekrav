"""Swedish descriptions from SCB's publication *SSYK 2012* (MIS 2012:1).

Used only for codes that JobTech lacks or merges. Only the description section is parsed: pages
whose running header names a "Yrkesområde". The overview list and appendices also contain code
lines and are skipped.
"""

from __future__ import annotations

import io
import json
import re
from pathlib import Path

from pypdf import PdfReader

from lonekrav.etl.http import cached_get

URL = ("https://www.scb.se/contentassets/c9d055b6f2114b62bd23c33602b56da5/"
       "ov9999_2012a01_br_x70br1201.pdf")
ENTRY = re.compile(r"^(\d{4})\s+([A-ZÅÄÖ].*)$")
HEADING = re.compile(r"^(Yrkesgrupp \d{3}|Huvudgrupp \d{2}|Yrkesområde \d)\b")
FOOTER = re.compile(r"^(\d+\s+)?Statistiska centralbyrån(\s+\d+)?\s*$")


def validate(data: bytes) -> None:
    if not PdfReader(io.BytesIO(data)).pages:
        raise ValueError("PDF has no pages")


def fetch(raw: Path, force: bool = False) -> Path:
    """Download the PDF and cache its page texts as JSON (pypdf is slow; do it once)."""
    pdf = cached_get("mis2012", URL, raw / "mis2012" / "ssyk2012.pdf", force=force,
                     validate=validate)
    out = raw / "mis2012" / "pages.json"
    if force or not out.exists():
        pages = [p.extract_text() or "" for p in PdfReader(io.BytesIO(pdf.read_bytes())).pages]
        out.write_text(json.dumps(dict(enumerate(pages)), ensure_ascii=False))
    return out


def load_pages(path: Path) -> dict[int, str]:
    return {int(k): v for k, v in json.loads(path.read_text()).items()}


def _is_description_page(text: str) -> bool:
    lines = text.splitlines()
    return bool(lines) and "Yrkesområde" in lines[0]


def _join(lines: list[str]) -> str:
    text = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if text.endswith("-") and line[:1].islower():
            text = text[:-1] + line  # re-join a word broken across lines
        elif text:
            text += "\n" + line if line.startswith(("–", "Hit hör")) else " " + line
        else:
            text = line
    return re.sub(r"\s+:", ":", text).strip()


def parse(pages: dict[int, str]) -> dict[str, str]:
    descriptions: dict[str, str] = {}
    code: str | None = None
    body: list[str] = []
    in_title = False

    def close():
        if code and body:
            descriptions[code] = _join(body)

    previous = None
    for number, text in sorted(pages.items()):
        if not _is_description_page(text):
            continue
        if previous is not None and number != previous + 1:
            close()  # never carry an entry across a gap in the page sequence
            code, body, in_title = None, [], False
        previous = number
        for line in text.splitlines()[1:]:
            if FOOTER.match(line.strip()):
                continue
            if m := ENTRY.match(line.strip()):
                close()
                code, body, in_title = m.group(1), [], True
            elif HEADING.match(line.strip()):
                close()
                code, body, in_title = None, [], False
            elif code:
                if in_title and line.startswith(" "):
                    continue  # title continuation such as " nivå 1"
                in_title = False
                body.append(line)
    close()
    return descriptions
