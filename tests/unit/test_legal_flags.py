import datetime as dt

from lonekrav.core.legal_flags import BANNED, EXEMPT_75, PARTIALLY_BANNED, flags_for

# Verbatim from SFS 2026:605, 5 kap. 6 § (published 23 May 2026).
SFS_EXEMPT = ["3115", "3215", "3511", "3512", "3513", "3514", "5321", "5322", "5323", "5324", "5325", "5326", "5330", "6121", "6129", "6130", "6210", "7212", "7215", "7233", "7413", "7611", "8161", "8169", "8199", "8341", "9210"]


def test_exempt_list_matches_ordinance():
    assert sorted(EXEMPT_75) == sorted(SFS_EXEMPT)
    assert len(EXEMPT_75) == 27


def test_bans():
    assert BANNED == {"5343"}
    assert PARTIALLY_BANNED == {"9210": "forest berry pickers only (bärplockare i skog)"}


def test_flags_for_codes():
    assert flags_for("2512") == []
    assert [f.kind for f in flags_for("3511")] == ["exempt_75"]
    assert [f.kind for f in flags_for("5343")] == ["banned"]
    assert [f.kind for f in flags_for("9210")] == ["exempt_75", "partially_banned"]


def test_every_flag_cites_the_ordinance():
    for code in ["3511", "5343", "9210"]:
        for f in flags_for(code):
            assert f.source.source == "sfs"
            assert f.source.ref.startswith("SFS 2026:605")
            assert f.effective_from == dt.date(2026, 6, 1)


def test_flags_carry_the_registrys_checked_on_date():  # Principle III
    from lonekrav.core.legal import load_registry

    checked = load_registry().code_lists["exempt_75"].source.checked_on
    assert [f.checked_on for f in flags_for("3511")] == [checked]
