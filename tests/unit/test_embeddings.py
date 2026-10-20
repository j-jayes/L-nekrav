import numpy as np

from lonekrav.core.embeddings import SPECS, FakeEmbedder


def test_fake_is_deterministic_and_normalised():
    e = FakeEmbedder(dim=64)
    a = e.encode_queries(["backend developer", "sjuksköterska"])
    b = e.encode_documents(["backend developer", "sjuksköterska"])
    assert a.shape == (2, 64)
    np.testing.assert_allclose(a, b)
    np.testing.assert_allclose(np.linalg.norm(a, axis=1), 1.0, rtol=1e-6)


def test_fake_similar_texts_score_higher():
    e = FakeEmbedder(dim=256)
    q, near, far = e.encode_queries(["backend developer python", "python backend developer apis",
                                     "sjuksköterska vård"])
    assert q @ near > q @ far


def test_registry_specs_without_loading_models():
    assert SPECS["kblab"].hf_id == "KBLab/sentence-bert-swedish-cased"
    assert SPECS["kblab"].dim == 768 and SPECS["kblab"].query_prompt_name is None
    h = SPECS["harrier"]
    assert h.hf_id == "microsoft/harrier-oss-v1-0.6b" and h.dim == 1024
    assert h.query_prompt_name == "web_search_query"
    assert h.dtype == "float32"  # bf16 is ~10x slower on CPU (references/embedding-benchmark.md)
