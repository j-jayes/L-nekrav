"""Probe for Feature 007: pool the cached Harrier vectors per SSYK code and check what a map of
them would show. Needs data/raw/embeddings (the index's cache) and, for the UMAP part, the `map`
dependency group:

    uv run --group map python references/occupation_map_probe.py data/raw/embeddings/harrier-6f0c7287a1e1.npz

Measured on 2026-10-27 (research.md R1-R3):

    codes 429 missing chunks 0 chunks/code min/median/max 2 10 177
    pairwise cosine p5/p50/p95/max 0.645 0.736 0.843 1.0
    2511 System analysts and ICT-architects -> [('2512', 0.939), ('2519', 0.935), ('1312', 0.921), ...]
    2221 Professional nurses -> [('2239', 0.921), ('5323', 0.905), ('5330', 0.9), ('2224', 0.895), ...]
    pairs > 0.99: 22, e.g. ('1311', '1312', 0.9982), ('1321', '1322', 1.0)
    nn=15 md=0.1: 2-D top10 within full top20 = 0.65; rerun identical=True; 5.9s
    nn=10 md=0.05: ... = 0.67;  nn=30 md=0.3: ... = 0.58
"""

import hashlib
import sys

import numpy as np

from lonekrav.core.chunks import chunk_profile
from lonekrav.core.profiles import load_profiles

profiles = load_profiles()
with np.load(sys.argv[1]) as z:
    cache = dict(zip(z["keys"].tolist(), z["vectors"], strict=True))
codes, vecs = [], []
for code, p in sorted(profiles.items()):
    rows = [cache[hashlib.sha256(c.text.encode()).hexdigest()] for c in chunk_profile(p)
            if c.kind in ("title", "desc_sv", "desc_en") and not c.ilo]
    m = np.mean(rows, axis=0)
    codes.append(code)
    vecs.append(m / np.linalg.norm(m))
X = np.stack(vecs)
S = X @ X.T
iu = np.triu_indices(len(codes), 1)
print("pairwise cosine p5/p50/p95/max", *np.round(np.percentile(S[iu], [5, 50, 95, 100]), 3))
for q in ["2511", "2221"]:
    i = codes.index(q)
    print(q, [(codes[j], round(float(S[i, j]), 3)) for j in np.argsort(-S[i])[1:6]])

import umap

full = np.argsort(-S, axis=1)[:, 1:21]
Y = umap.UMAP(n_neighbors=15, min_dist=0.1, metric="cosine", random_state=0, n_jobs=1).fit_transform(X)
D = ((Y[:, None] - Y[None]) ** 2).sum(-1)
np.fill_diagonal(D, np.inf)
two = np.argsort(D, axis=1)[:, :10]
print("2-D top10 within full top20 =", np.mean([len(set(two[i]) & set(full[i])) / 10 for i in range(len(codes))]))
