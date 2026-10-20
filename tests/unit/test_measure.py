from lonekrav.etl.measure import Result, render


def test_render_table():
    md = render([
        Result(model="KBLab/sentence-bert-swedish-cased", dtype="float32", dim=768, max_seq=384,
               load_s=5.3, peak_gb=0.73, short_ms=(39, 48), ad_ms=(81, 89), doc_ms=17),
    ], machine="Apple M2 Pro", date="2026-10-20")
    assert "| KBLab/sentence-bert-swedish-cased | float32 | 768 | 384 | 5 s | 0.73 GB |" in md
    assert "39 / 48 ms" in md and "81 / 89 ms" in md and "17 ms" in md
    assert "Apple M2 Pro" in md and "2026-10-20" in md
