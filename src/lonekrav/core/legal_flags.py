"""Occupation-level rules from SFS 2026:605 (utlänningsförordningen 5 kap. 5–6 §§).

The code lists live in the legal registry (`legal_constants.yaml`); this module turns them into the
flags attached to occupation profiles, search hits and comparison columns.
"""

from __future__ import annotations

from lonekrav.core.legal import CodeList, load_registry
from lonekrav.core.models import LegalFlag, SourceRef

_LISTS = load_registry().code_lists
EXEMPT_75 = frozenset(_LISTS["exempt_75"].codes)
BANNED = set(_LISTS["banned"].codes)
PARTIALLY_BANNED = dict(_LISTS["partially_banned"].codes)
_PARAGRAPH = {"exempt_75": "6 §", "banned": "5 §", "partially_banned": "5 §"}


def _flag(cl: CodeList, code: str) -> LegalFlag:
    return LegalFlag(kind=cl.kind, note=cl.codes[code] or cl.note,
                     effective_from=cl.effective_from, checked_on=cl.source.checked_on,
                     source=SourceRef(source="sfs", ref=f"SFS 2026:605, 5 kap. {_PARAGRAPH[cl.kind]}",
                                      url=cl.source.url))


def flags_for(code: str) -> list[LegalFlag]:
    return [_flag(cl, code) for cl in _LISTS.values() if code in cl.codes]
