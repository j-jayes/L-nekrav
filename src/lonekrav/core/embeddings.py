"""Embedding models behind one small protocol, plus an offline fake for tests."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from functools import cache
from typing import Protocol

import numpy as np


class Embedder(Protocol):
    name: str
    dim: int

    def encode_queries(self, texts: list[str]) -> np.ndarray: ...
    def encode_documents(self, texts: list[str]) -> np.ndarray: ...


@dataclass(frozen=True)
class Spec:
    hf_id: str
    dim: int
    query_prompt_name: str | None
    dtype: str = "float32"


SPECS = {
    "kblab": Spec("KBLab/sentence-bert-swedish-cased", 768, None),
    # Harrier ships bf16 weights; on CPU they are ~10x slower than fp32 (measured 2026-10-20).
    "harrier": Spec("microsoft/harrier-oss-v1-0.6b", 1024, "web_search_query"),
}


class SentenceTransformerEmbedder:
    def __init__(self, name: str, spec: Spec, batch_size: int = 16):
        import torch
        from sentence_transformers import SentenceTransformer

        self.name, self.dim, self.spec, self.batch_size = name, spec.dim, spec, batch_size
        self.model = SentenceTransformer(spec.hf_id, device="cpu",
                                         model_kwargs={"torch_dtype": getattr(torch, spec.dtype)})

    def _encode(self, texts, **kw) -> np.ndarray:
        return self.model.encode(texts, batch_size=self.batch_size, normalize_embeddings=True,
                                 convert_to_numpy=True, **kw).astype(np.float32)

    def encode_queries(self, texts: list[str]) -> np.ndarray:
        kw = {"prompt_name": self.spec.query_prompt_name} if self.spec.query_prompt_name else {}
        return self._encode(texts, **kw)

    def encode_documents(self, texts: list[str]) -> np.ndarray:
        return self._encode(texts, show_progress_bar=len(texts) > 100)


@cache
def get_embedder(name: str) -> Embedder:
    return SentenceTransformerEmbedder(name, SPECS[name])


class FakeEmbedder:
    """Hashed bag of words: deterministic, offline, good enough to test plumbing."""

    def __init__(self, dim: int = 64, name: str = "fake"):
        self.name, self.dim = name, dim

    def _vec(self, text: str) -> np.ndarray:
        v = np.zeros(self.dim, dtype=np.float32)
        for tok in re.findall(r"\w+", text.casefold()):
            v[int(hashlib.md5(tok.encode()).hexdigest(), 16) % self.dim] += 1.0
        n = np.linalg.norm(v)
        return v / n if n else v

    def encode_queries(self, texts: list[str]) -> np.ndarray:
        return np.stack([self._vec(t) for t in texts])

    encode_documents = encode_queries
