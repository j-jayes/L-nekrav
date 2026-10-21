"""Occupation-level rules from SFS 2026:605 (utlänningsförordningen 5 kap. 5–6 §§).

This is data, not logic: when the ordinance changes, edit these sets and the test that quotes it.
"""

from __future__ import annotations

import datetime as dt

from lonekrav.core.models import LegalFlag, SourceRef

SFS_URL = "https://svenskforfattningssamling.se/doc/2026605.html"
EFFECTIVE = dt.date(2026, 6, 1)

# 5 kap. 6 §: the 90 % salary requirement does not apply; 75 % of the median applies instead.
EXEMPT_75 = frozenset(["3115", "3215", "3511", "3512", "3513", "3514", "5321", "5322", "5323", "5324", "5325", "5326", "5330", "6121", "6129", "6130", "6210", "7212", "7215", "7233", "7413", "7611", "8161", "8169", "8199", "8341", "9210"])

# 5 kap. 5 §: work permits may not be granted.
BANNED = {"5343"}
PARTIALLY_BANNED = {"9210": "forest berry pickers only (bärplockare i skog)"}


def _ref(paragraph: str) -> SourceRef:
    return SourceRef(source="sfs", ref=f"SFS 2026:605, 5 kap. {paragraph}", url=SFS_URL)


def flags_for(code: str) -> list[LegalFlag]:
    flags = []
    if code in EXEMPT_75:
        flags.append(LegalFlag(kind="exempt_75", note="75 % of the median applies instead of 90 %",
                               effective_from=EFFECTIVE, source=_ref("6 §")))
    if code in BANNED:
        flags.append(LegalFlag(kind="banned", effective_from=EFFECTIVE, source=_ref("5 §")))
    if code in PARTIALLY_BANNED:
        flags.append(LegalFlag(kind="partially_banned", note=PARTIALLY_BANNED[code],
                               effective_from=EFFECTIVE, source=_ref("5 §")))
    return flags
