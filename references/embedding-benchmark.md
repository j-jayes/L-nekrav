# Embedding model measurements

Measured 2026-10-20 on an Apple M2 Pro (10 cores, 16 GB), CPU only, sentence-transformers 6.1,
Python 3.12. The script was a scratch probe; `lonekrav-etl measure-models` will regenerate this
file. "Short query" is "backend developer". "Ad" is a 600-word English job ad. Documents are about
80-word Swedish descriptions, batch 32. Peak is process max RSS, including the batch-32 encode.

| Model | dtype | Dim | Max seq | Load | Peak RSS | Short query p50 / p95 | Ad p50 / p95 | Per document |
|---|---|---|---|---|---|---|---|---|
| KBLab/sentence-bert-swedish-cased | fp32 | 768 | 384 | 5 s | 0.73 GB | 39 / 48 ms | 81 / 89 ms | 17 ms |
| microsoft/harrier-oss-v1-0.6b | bf16 (checkpoint default) | 1024 | 32 768 | 193 s (first, download) | 1.27 GB | 163 / 191 ms | 5 856 / 6 097 ms | 1 226 ms |
| microsoft/harrier-oss-v1-0.6b | fp32 | 1024 | 32 768 | 7 s | 3.10 GB | 130 / 137 ms | 582 / 608 ms | 130 ms |

Findings:

- **Load Harrier in float32 on CPU.** The checkpoint loads as bfloat16 by default, and bf16 matrix
  maths is about 10× slower on this CPU. Pass `model_kwargs={"torch_dtype": torch.float32}`.
- KBLab is fast enough for keystroke search: about 40 ms per query.
- KBLab truncates at 384 tokens, which confirms the chunking decision (research R7).
- Harrier fp32 plus KBLab needs about 3.5–4 GB at peak, over the 2.5 GB budget in the original plan.
- Indexing about 4 000 chunks with Harrier fp32 takes about 9 minutes, within SC-007.
