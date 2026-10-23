from lonekrav.core.chunks import MAX_CHARS, MAX_LABELS, chunk_profile
from lonekrav.core.models import OccupationProfile, SourceRef, Synonym, Text

S = SourceRef(source="scb_structure", ref="r", url="u")


def profile(n_sv_labels=95, long_text=False):
    sv_text = ("Analyserar och utvecklar IT-system. " * (120 if long_text else 3)).strip()
    return OccupationProfile(
        code="2512", title_sv="Mjukvaru- och systemutvecklare m.fl.",
        title_en="Software- and system developers", isco_codes=["2512"],
        descriptions=[Text(lang="sv", kind="definition", text=sv_text, source=S),
                      Text(lang="en", kind="tasks", text="(a) designing software;", source=S)],
        synonyms=[Synonym(lang="sv", label=f"Utvecklare {i}", source=S) for i in range(n_sv_labels)]
        + [Synonym(lang="en", label="Backend developer", source=S),
           Synonym(lang="en", label="Software engineer", source=S)],
        sources=[S],
    )


def test_chunk_kinds_and_ids():
    chunks = chunk_profile(profile())
    kinds = [c.kind for c in chunks]
    assert kinds[0] == "title" and "Software- and system developers" in chunks[0].text
    assert {"desc_sv", "desc_en", "synonyms_sv", "synonyms_en"} <= set(kinds)
    assert len({c.chunk_id for c in chunks}) == len(chunks)
    assert all(c.chunk_id.startswith("2512:") and c.code == "2512" for c in chunks)


def test_limits():
    chunks = chunk_profile(profile(long_text=True))
    assert all(len(c.text) <= MAX_CHARS for c in chunks)
    syn = [c for c in chunks if c.kind == "synonyms_sv"]
    assert len(syn) == 3  # 95 labels in groups of at most 40
    assert all(c.text.count(";") < MAX_LABELS for c in syn)
    assert sum(1 for c in chunks if c.kind == "desc_sv") >= 2  # long text split


def test_holdout_titles_removed_everywhere():
    held = {"backend developer", "utvecklare 3"}
    text = " ".join(c.text for c in chunk_profile(profile(), holdout=held)).casefold()
    assert "backend developer" not in text
    assert "utvecklare 3;" not in text and not text.endswith("utvecklare 3")
    assert "software engineer" in text


def test_synonym_chunks_respect_the_character_limit():
    """Copilot review on PR #1: 40 labels of 50+ characters overflowed MAX_CHARS."""
    p = profile(n_sv_labels=0).model_copy(update={"synonyms": [
        Synonym(lang="sv", label=f"Mycket långt yrkesnamn nummer {i:03d} " + "x" * 30, source=S)
        for i in range(120)]})
    syn = [c for c in chunk_profile(p) if c.kind == "synonyms_sv"]
    assert all(len(c.text) <= MAX_CHARS for c in syn)
    assert sum(c.text.count(";") + 1 for c in syn) == 120  # no label lost


ILO = SourceRef(source="ilo_isco08", ref="ISCO-08", url="u")


def test_ilo_chunks_are_flagged_and_their_text_is_unchanged():
    """ILO reserves reproduction rights: its text may rank but is never shown (Feature 004)."""
    plain = profile(n_sv_labels=3)
    with_ilo = plain.model_copy(update={
        "descriptions": [*plain.descriptions,
                         Text(lang="en", kind="tasks", text="(a) writing ILO tasks;", source=ILO)],
        "synonyms": [*plain.synonyms, Synonym(lang="en", label="Ilo example title", source=ILO)]})
    chunks = chunk_profile(with_ilo)
    flagged = {c.text for c in chunks if c.ilo}
    assert "(a) writing ILO tasks;" in flagged
    assert any("Ilo example title" in t and "Backend developer" in t for t in flagged)  # a mixed batch
    assert not any(c.ilo for c in chunk_profile(plain))
    assert [c.text for c in chunks if c.kind != "desc_en"] == [  # batching is unchanged
        c.text for c in chunk_profile(with_ilo.model_copy(update={"synonyms": [
            s.model_copy(update={"source": S}) for s in with_ilo.synonyms]})) if c.kind != "desc_en"]
