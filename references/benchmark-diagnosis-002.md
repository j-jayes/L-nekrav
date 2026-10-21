# Benchmark diagnosis, Feature 002

Spec FR-018–FR-020a; research R1. Regenerate with
`uv run lonekrav-etl build && uv run lonekrav-etl index && uv run lonekrav-etl benchmark`.

## 1. After the leak fix (T017, 2026-10-21)

Change: the hold-out check counts a query as present when followed by up to three word characters
(FR-018a), in both languages, and a pair whose English ESCO preferred label leaks falls back to
ESCO's other English labels. No search change yet.

```text
built 429 profiles, 5160 distributions, 36120 age rows, 333 generated queries (152 with English)
index 9551 chunks from 429 profiles (580 held out)
method   lang  set           R@1    R@5    MRR    n
kblab    en    all_paired    0.543  0.870  0.685  184
kblab    en    generated     0.546  0.849  0.676  152
kblab    en    handwritten   0.531  0.969  0.727  32
kblab    sv    all_paired    0.582  0.832  0.681  184
kblab    sv    generated     0.566  0.803  0.659  152
kblab    sv    generated_sv_only 0.326  0.646  0.460  181
kblab    sv    handwritten   0.656  0.969  0.786  32
harrier  en    all_paired    0.707  0.924  0.798  184
harrier  en    generated     0.724  0.914  0.807  152
harrier  en    handwritten   0.625  0.969  0.753  32
harrier  sv    all_paired    0.679  0.924  0.782  184
harrier  sv    generated     0.691  0.914  0.790  152
harrier  sv    generated_sv_only 0.420  0.751  0.557  181
harrier  sv    handwritten   0.625  0.969  0.747  32
bm25     en    all_paired    0.641  0.848  0.726  184
bm25     en    generated     0.678  0.842  0.751  152
bm25     en    handwritten   0.469  0.875  0.603  32
bm25     sv    all_paired    0.408  0.560  0.479  184
bm25     sv    generated     0.421  0.546  0.480  152
bm25     sv    generated_sv_only 0.304  0.414  0.350  181
bm25     sv    handwritten   0.344  0.625  0.474  32
fused    en    all_paired    0.739  0.918  0.816  184
fused    en    generated     0.750  0.908  0.815  152
fused    en    handwritten   0.688  0.969  0.821  32
fused    sv    all_paired    0.707  0.918  0.796  184
fused    sv    generated     0.697  0.921  0.792  152
fused    sv    generated_sv_only 0.442  0.746  0.569  181
fused    sv    handwritten   0.750  0.906  0.814  32
fused_fast en    all_paired    0.696  0.891  0.782  184
fused_fast en    generated     0.684  0.875  0.772  152
fused_fast en    handwritten   0.750  0.969  0.831  32
fused_fast sv    all_paired    0.641  0.837  0.718  184
fused_fast sv    generated     0.658  0.836  0.724  152
fused_fast sv    generated_sv_only 0.414  0.674  0.522  181
fused_fast sv    handwritten   0.562  0.844  0.686  32
gap diagnosis (fused, paired n=184, gap=0.000)
origin       form    n    R@5 en  R@5 sv  gap pts  share
generated    single  129  0.899   0.915   -0.011   -
generated    slash   23   0.957   0.957   +0.000   -
handwritten  single  32   0.969   0.906   +0.011   -
vs benchmark_results_001.json (2026-10-21T12:37:50+00:00)
fused R@5 en 0.993 -> 0.918; sv 0.895 -> 0.918
paired n 143 -> 184; gap 0.098 -> 0.000; overlap 0.688 -> 0.688
```

Reading:

- **The 9.8-point gap was the benchmark.** With leaking English queries replaced, paired n rose from
  143 to 184 and full-mode fused Recall@5 is 0.918 in both languages (gap 0.000). The 001 English
  figure (0.993) was inflated by lookups; Swedish rose from 0.895 to 0.918 on the larger set.
- **Slash-joined queries are not the problem**: 23 paired slash queries score 0.957 in both languages.
- **Still failing**: fused (0.918) is below Harrier alone (0.924) in both languages, and hand-written
  top-5 overlap is 0.688 against 0.80. Swedish BM25 (0.560 paired) is the weak method.

## 2. Fusion weights (T020, 2026-10-21)

Swedish BM25 (0.546 Recall@5 on generated Swedish) pulled the equal-weight fusion below Harrier
alone. Sweep: RRF weight 0.0–1.0 in steps of 0.1 for kblab and bm25, Harrier fixed at 1.0, chosen
on the 152 generated paired queries by the higher worst-language Recall@5, then the higher mean;
confirmed on the 32 hand-written pairs, which played no part in the choice (FR-020a). Script:
`sweep.py` in the session scratchpad; output:

```text
single methods (gen en/sv | hw en/sv): {'kblab': ([0.8486842105263158, 0.7960526315789473], [0.96875, 0.96875]), 'harrier': ([0.9144736842105263, 0.9013157894736842], [0.96875, 0.96875]), 'bm25': ([0.8421052631578947, 0.5460526315789473], [0.875, 0.625])}
top 10 on generated (min, mean, w_kblab, w_bm25, en, sv):
   [0.921, 0.924, 1.0, 0.3, 0.928, 0.921]
   [0.921, 0.924, 0.2, 0.3, 0.928, 0.921]
   [0.921, 0.921, 1.0, 0.6, 0.921, 0.921]
   [0.921, 0.921, 1.0, 0.5, 0.921, 0.921]
   [0.921, 0.921, 0.3, 0.3, 0.921, 0.921]
   [0.921, 0.921, 0.2, 0.5, 0.921, 0.921]
   [0.921, 0.921, 0.2, 0.4, 0.921, 0.921]
   [0.921, 0.921, 0.2, 0.1, 0.921, 0.921]
   [0.914, 0.921, 1.0, 0.8, 0.914, 0.928]
   [0.914, 0.921, 1.0, 0.4, 0.928, 0.914]
w_kblab=1.0 w_bm25=1.0: gen en/sv (0.9078947368421053, 0.9210526315789473)  hw en/sv/overlap (0.96875, 0.90625, 0.6875)  all (0.9184782608695652, 0.9184782608695652, 0.3695652173913043)
w_kblab=1.0 w_bm25=0.3: gen en/sv (0.9276315789473685, 0.9210526315789473)  hw en/sv/overlap (1.0, 1.0, 0.875)  all (0.9402173913043478, 0.9347826086956522, 0.44565217391304346)
w_kblab=0.2 w_bm25=0.3: gen en/sv (0.9276315789473685, 0.9210526315789473)  hw en/sv/overlap (1.0, 1.0, 0.53125)  all (0.9402173913043478, 0.9347826086956522, 0.34782608695652173)
w_kblab=1.0 w_bm25=0.6: gen en/sv (0.9210526315789473, 0.9210526315789473)  hw en/sv/overlap (1.0, 1.0, 0.78125)  all (0.9347826086956522, 0.9347826086956522, 0.40217391304347827)
w_kblab=1.0 w_bm25=0.5: gen en/sv (0.9210526315789473, 0.9210526315789473)  hw en/sv/overlap (1.0, 1.0, 0.84375)  all (0.9347826086956522, 0.9347826086956522, 0.43478260869565216)
w_kblab=0.3 w_bm25=0.3: gen en/sv (0.9210526315789473, 0.9210526315789473)  hw en/sv/overlap (1.0, 1.0, 0.625)  all (0.9347826086956522, 0.9347826086956522, 0.3641304347826087)
```

Choice: **bm25 weight 0.3, kblab and Harrier 1.0** (top of the generated ranking and the simplest:
one method changes). On the hand-written pairs Recall@5 rises from 0.969/0.906 to 1.0/1.0 and
top-5 overlap from 0.688 to 0.875. The next-best candidate with kblab at 0.2 scores the same on the
generated set but drops hand-written overlap to 0.53, which is why the confirmation set matters.
