"""Milvus collection of occupation chunks: one dense field per model plus BM25.

Pattern from references/milvus_lite_hybrid.py. A local file path runs Milvus Lite; set
MILVUS_URI to use a Milvus server instead.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

# isort: off
# torch must load before pymilvus: faiss (inside Milvus Lite) and torch each bundle libomp on
# macOS, and if faiss's loads first the first torch operation segfaults.
import torch  # noqa: F401
import numpy as np
from pymilvus import DataType, Function, FunctionType, MilvusClient
# isort: on

from lonekrav.core.chunks import MAX_CHARS, Chunk
from lonekrav.core.text import analyze, profile_vocab

COLLECTION = "occupation_chunks"
DEFAULT_DB = Path("data/lonekrav_milvus.db")
FIELDS = ("chunk_id", "code", "kind", "lang", "text", "ilo")


def bm25_score(distance: float) -> float:
    """BM25 scores are positive; Milvus Lite reports them negated."""
    return abs(distance)


class Store:
    def __init__(self, uri: str | Path | None = None, dims: dict[str, int] | None = None,
                 vocab: frozenset[str] | None = None):
        self.uri = os.environ.get("MILVUS_URI") or str(uri or DEFAULT_DB)
        if not self.uri.startswith("http"):
            Path(self.uri).parent.mkdir(parents=True, exist_ok=True)
        self.client = MilvusClient(self.uri)
        self.dims = dims or {}
        self._vocab = vocab
        if self.client.has_collection(COLLECTION):
            self.client.load_collection(COLLECTION)  # a reopened index starts "released"

    @property
    def _vocab_file(self) -> Path | None:
        """The analysis vocabulary is saved beside a local index, so reopening it (or a copy of
        it) analyses queries exactly as the documents were analysed."""
        return None if self.uri.startswith("http") else Path(self.uri + ".vocab.json")

    def create(self) -> None:
        if self.client.has_collection(COLLECTION):
            self.client.drop_collection(COLLECTION)
        s = self.client.create_schema(auto_id=False)
        s.add_field("chunk_id", DataType.VARCHAR, max_length=64, is_primary=True)
        s.add_field("code", DataType.VARCHAR, max_length=4)
        s.add_field("kind", DataType.VARCHAR, max_length=16)
        s.add_field("lang", DataType.VARCHAR, max_length=8)
        s.add_field("text", DataType.VARCHAR, max_length=MAX_CHARS * 4)
        s.add_field("ilo", DataType.BOOL)
        s.add_field("bm25_text", DataType.VARCHAR, max_length=MAX_CHARS * 12,
                    enable_analyzer=True, analyzer_params={"type": "standard"})
        s.add_field("bm25", DataType.SPARSE_FLOAT_VECTOR)
        s.add_function(Function(name="bm25_fn", function_type=FunctionType.BM25,
                                input_field_names=["bm25_text"], output_field_names=["bm25"]))
        ip = self.client.prepare_index_params()
        ip.add_index("bm25", index_type="SPARSE_INVERTED_INDEX", metric_type="BM25")
        for name, dim in self.dims.items():
            s.add_field(f"vec_{name}", DataType.FLOAT_VECTOR, dim=dim)
            ip.add_index(f"vec_{name}", index_type="FLAT", metric_type="COSINE")
        self.client.create_collection(COLLECTION, schema=s, index_params=ip)
        if self._vocab_file:
            self._vocab_file.write_text(json.dumps(sorted(self.vocab), ensure_ascii=False))

    def insert(self, chunks: list[Chunk], vectors: dict[str, np.ndarray], batch: int = 500) -> None:
        rows = []
        for i, c in enumerate(chunks):
            row = c.model_dump() | {"bm25_text": analyze(c.text, self.vocab)}
            row |= {f"vec_{n}": v[i].tolist() for n, v in vectors.items()}
            rows.append(row)
        for i in range(0, len(rows), batch):
            self.client.insert(COLLECTION, rows[i:i + batch])
        self.client.load_collection(COLLECTION)

    def _hits(self, res, score) -> list[dict]:
        return [{**h["entity"], "score": score(h["distance"])} for h in res[0]]

    def search_dense(self, name: str, vector: np.ndarray, limit: int) -> list[dict]:
        res = self.client.search(COLLECTION, data=[vector.tolist()], anns_field=f"vec_{name}",
                                 limit=limit, output_fields=list(FIELDS),
                                 search_params={"metric_type": "COSINE"})
        return self._hits(res, float)

    def search_bm25(self, text: str, limit: int) -> list[dict]:
        res = self.client.search(COLLECTION, data=[analyze(text, self.vocab)], anns_field="bm25",
                                 limit=limit,
                                 output_fields=list(FIELDS), search_params={"metric_type": "BM25"})
        return self._hits(res, bm25_score)

    @property
    def vocab(self) -> frozenset[str]:
        if self._vocab is None and self._vocab_file and self._vocab_file.exists():
            self._vocab = frozenset(json.loads(self._vocab_file.read_text()))
        if self._vocab is None:  # a Milvus server index: rebuild from the committed profiles
            from lonekrav.core.profiles import load_profiles

            self._vocab = profile_vocab(load_profiles().values())
        return self._vocab

    def count(self) -> int:
        return self.client.query(COLLECTION, filter="", output_fields=["count(*)"])[0]["count(*)"]
