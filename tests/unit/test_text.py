from lonekrav.core.text import analyze, build_vocab

VOCAB = build_vocab(["Backend-utvecklare och frontend-utvecklare", "Utvecklare inom spel",
                     "Sjuksköterskor på sjukhus", "backend system"])


def toks(text, vocab=VOCAB):
    return set(analyze(text, vocab).split())


def test_inflections_share_a_stem():
    assert toks("sjuksköterska") & toks("sjuksköterskor")
    assert "develop" in toks("developer") & toks("developers")


def test_closed_compound_matches_hyphenated_form():
    assert {"backend", *toks("utvecklare")} <= toks("backendutvecklare")
    assert toks("backendutvecklare") & toks("Backend-utvecklare") >= toks("utvecklare")


def test_linking_s_is_handled():
    v = build_vocab(["system", "utvecklare", "system"])
    assert toks("systemsutvecklare", v) >= toks("utvecklare", v) | toks("system", v)


def test_short_or_unknown_words_are_left_alone():
    assert toks("xyzzyplughfoo") == {"xyzzyplughfoo"}
    assert toks("IT") == {"it"}


def test_deterministic_string():
    assert analyze("Backend-utvecklare", VOCAB) == analyze("Backend-utvecklare", VOCAB)


def test_inflected_compound_tail_still_splits():
    assert toks("utvecklare") & toks("backendutvecklaren")
    assert "backend" in toks("backendutvecklaren")
