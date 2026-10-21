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


def test_document_cache_only_encodes_new_texts(tmp_path):
    from lonekrav.core.embeddings import encode_documents_cached

    class Counting(FakeEmbedder):
        def __init__(self):
            super().__init__(dim=16, name="count")
            self.seen = []

        def encode_documents(self, texts):
            self.seen += texts
            return super().encode_documents(texts)

    e = Counting()
    first = encode_documents_cached(e, ["a b", "c d"], tmp_path)
    again = encode_documents_cached(e, ["c d", "e f", "a b"], tmp_path)
    assert e.seen == ["a b", "c d", "e f"]  # "a b" and "c d" came from the cache
    np.testing.assert_allclose(again[0], first[1])
    np.testing.assert_allclose(again[2], first[0])
    assert again.shape == (3, 16) and again.dtype == np.float32


def test_document_cache_is_per_model(tmp_path):
    from lonekrav.core.embeddings import encode_documents_cached

    a = encode_documents_cached(FakeEmbedder(dim=8, name="a"), ["x"], tmp_path)
    b = encode_documents_cached(FakeEmbedder(dim=16, name="b"), ["x"], tmp_path)
    assert a.shape == (1, 8) and b.shape == (1, 16)
