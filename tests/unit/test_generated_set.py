from lonekrav.core.profiles import build_profiles
from lonekrav.etl.benchmark import generate_queries


def test_generated_set_is_stable_and_one_per_group(inputs):
    profiles = build_profiles(inputs)
    a, held_a = generate_queries(inputs, profiles, seed=7)
    b, held_b = generate_queries(inputs, profiles, seed=7)
    assert [q.model_dump() for q in a] == [q.model_dump() for q in b] and held_a == held_b
    groups = [tuple(q.expected_codes) for q in a]
    assert len(groups) == len(set(groups))  # at most one query per occupation (or merged pair)
    assert all(q.origin == "generated" and q.type == "title" for q in a)


def test_merged_manager_names_accept_both_levels(inputs):
    qs, _ = generate_queries(inputs, build_profiles(inputs), seed=7)
    assert any(q.expected_codes == ["1211", "1212"] for q in qs)


def test_never_samples_an_official_title(inputs):
    profiles = build_profiles(inputs)
    titles = {p.title_sv.casefold() for p in profiles.values()}
    qs, _ = generate_queries(inputs, profiles, seed=7)
    assert not {q.text_sv.casefold() for q in qs} & titles


def test_english_only_from_exact_or_close_esco_and_everything_held_out(inputs):
    profiles = build_profiles(inputs)
    qs, held = generate_queries(inputs, profiles, seed=7)
    assert any(q.text_en for q in qs)
    for q in qs:
        assert q.text_sv.casefold() in held
        if q.text_en:
            assert q.text_en.casefold() in held


def test_query_phrases_appear_in_no_indexed_chunk_of_their_answer(inputs):
    """Copilot review on PR #1: holding out whole labels left the phrase in titles, descriptions
    and longer labels ('Minister' in 'Minister, statsråd'), so the benchmark rewarded lookup."""
    import re

    from lonekrav.core.chunks import chunk_profile
    from lonekrav.core.profiles import attach_ilo

    profiles = build_profiles(inputs)
    qs, held = generate_queries(inputs, profiles, seed=7)
    indexed = attach_ilo(profiles, inputs.ilo, inputs.isco_key)
    for q in qs:
        text = " ".join(c.text for code in q.expected_codes
                        for c in chunk_profile(indexed[code], holdout=held)).casefold()
        for phrase in filter(None, (q.text_sv, q.text_en)):
            assert not re.search(rf"(?<!\w){re.escape(phrase.casefold())}(?!\w)", text), (q.id, phrase)


def test_a_leaking_title_is_not_sampled(inputs):
    profiles = build_profiles(inputs)
    name = next(n for n in inputs.jobtech["2512"].names)
    leaky = profiles["2512"].model_copy(update={"title_sv": f"{name.label} m.fl."})
    qs, _ = generate_queries(inputs, profiles | {"2512": leaky}, seed=7)
    assert all(q.text_sv != name.label for q in qs)
