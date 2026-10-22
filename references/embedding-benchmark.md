# Embedding model measurements

Measured 2026-10-20 on Apple M2 Pro, CPU only, by `lonekrav-etl measure-models`. Short query is
"backend developer"; ad is a 600-word English job ad; documents are about 80-word Swedish
descriptions in batches of 32. Peak is the model process's max RSS.

| Model | dtype | Dim | Max seq | Load | Peak RSS | Short query p50 / p95 | Ad p50 / p95 | Per document |
|---|---|---|---|---|---|---|---|---|
| KBLab/sentence-bert-swedish-cased | float32 | 768 | 384 | 3 s | 0.96 GB | 40 / 56 ms | 78 / 95 ms | 17 ms |
| microsoft/harrier-oss-v1-0.6b | float32 | 1024 | 32768 | 7 s | 2.56 GB | 124 / 142 ms | 648 / 695 ms | 164 ms |
| microsoft/harrier-oss-v1-0.6b | bfloat16 | 1024 | 32768 | 5 s | 1.54 GB | 139 / 181 ms | 5971 / 6112 ms | 1231 ms |

Harrier is loaded in float32: its bfloat16 checkpoint is far slower on CPU.
The container memory cap is 5 GB (4 GB from 2026-10-20; raised on 2026-10-22 after measuring the container, references/container-memory.md).
