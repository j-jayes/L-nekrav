"""Embedding models behind one small protocol, plus an offline fake for tests."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Protocol

import numpy as np


class Embedder(Protocol):
    name: str
    dim: int
    identity: str  # model id, revision and settings: what the document cache is keyed by

    def encode_queries(self, texts: list[str]) -> np.ndarray: ...
    def encode_documents(self, texts: list[str]) -> np.ndarray: ...


@dataclass(frozen=True)
class Spec:
    hf_id: str
    revision: str  # pinned, so an index and its queries always use the same weights
    dim: int
    query_prompt_name: str | None
    dtype: str = "float32"
    query_threads: int | None = None  # torch threads for query encoding; None keeps the default


SPECS = {
    "kblab": Spec("KBLab/sentence-bert-swedish-cased", "6b5e83cd29c03729cfdc33d13b1423399b0efb5c",
                  768, None, query_threads=1),  # 1 thread is faster for short queries (R2)
    # Harrier ships bf16 weights; on CPU they are ~10x slower than fp32 (measured 2026-10-20).
    "harrier": Spec("microsoft/harrier-oss-v1-0.6b", "f9b9dc8d367d443f2479d27aa5d8d2850c0774ee",
                    1024, "web_search_query"),
}


class SentenceTransformerEmbedder:
    def __init__(self, name: str, spec: Spec, batch_size: int = 16):
        import torch
        from sentence_transformers import SentenceTransformer

        self.name, self.dim, self.spec, self.batch_size = name, spec.dim, spec, batch_size
        self.identity = f"{spec.hf_id}@{spec.revision}:{spec.dim}:{spec.dtype}"
        self.model = SentenceTransformer(spec.hf_id, revision=spec.revision, device="cpu",
                                         model_kwargs={"torch_dtype": getattr(torch, spec.dtype)})

    def _encode(self, texts, **kw) -> np.ndarray:
        return self.model.encode(texts, batch_size=self.batch_size, normalize_embeddings=True,
                                 convert_to_numpy=True, **kw).astype(np.float32)

    def encode_queries(self, texts: list[str]) -> np.ndarray:
        import torch

        kw = {"prompt_name": self.spec.query_prompt_name} if self.spec.query_prompt_name else {}
        if not self.spec.query_threads:
            return self._encode(texts, **kw)
        before = torch.get_num_threads()
        torch.set_num_threads(self.spec.query_threads)
        try:
            return self._encode(texts, **kw)
        finally:
            torch.set_num_threads(before)

    def encode_documents(self, texts: list[str]) -> np.ndarray:
        return self._encode(texts, show_progress_bar=len(texts) > 100)


@cache
def get_embedder(name: str) -> Embedder:
    return SentenceTransformerEmbedder(name, SPECS[name])


class FakeEmbedder:
    """Hashed bag of words: deterministic, offline, good enough to test plumbing."""

    def __init__(self, dim: int = 64, name: str = "fake"):
        self.name, self.dim = name, dim
        self.identity = f"fake:{dim}"

    def _vec(self, text: str) -> np.ndarray:
        v = np.zeros(self.dim, dtype=np.float32)
        for tok in re.findall(r"\w+", text.casefold()):
            v[int(hashlib.md5(tok.encode()).hexdigest(), 16) % self.dim] += 1.0
        n = np.linalg.norm(v)
        return v / n if n else v

    def encode_queries(self, texts: list[str]) -> np.ndarray:
        return np.stack([self._vec(t) for t in texts])

    encode_documents = encode_queries


def encode_documents_cached(emb: Embedder, texts: list[str], cache_dir: Path) -> np.ndarray:
    """Encode documents, reusing vectors cached by (model identity, text hash) under `cache_dir`.

    A rebuild then re-embeds only chunks whose text changed (Harrier: ~20 min for a full pass).
    """
    path = cache_dir / f"{emb.name}-{hashlib.sha256(emb.identity.encode()).hexdigest()[:12]}.npz"
    cached: dict[str, np.ndarray] = {}
    if path.exists():
        with np.load(path) as z:
            cached = dict(zip(z["keys"].tolist(), z["vectors"], strict=True))
    keys = [hashlib.sha256(t.encode()).hexdigest() for t in texts]
    todo = list({k: t for k, t in zip(keys, texts, strict=True) if k not in cached}.items())
    if todo:
        new = emb.encode_documents([t for _, t in todo])
        cached.update(zip([k for k, _ in todo], new, strict=True))
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(path, keys=np.array(list(cached)), vectors=np.stack(list(cached.values())))
    return np.stack([cached[k] for k in keys]).astype(np.float32)
