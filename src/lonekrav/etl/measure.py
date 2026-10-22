"""Measure embedding-model latency and memory on this machine -> references/embedding-benchmark.md.

Each model runs in its own subprocess so peak memory is per model, not cumulative.
"""

from __future__ import annotations

import datetime as dt
import json
import platform
import subprocess
import sys
from pathlib import Path

from pydantic import BaseModel

OUT = Path("references/embedding-benchmark.md")
SHORT = "backend developer"
AD = ("We are looking for a backend developer who designs, builds and maintains APIs and data "
      "pipelines in Python. You will work closely with product and data teams, review code, "
      "write tests and operate services in the cloud. ") * 14  # about 600 words
DOC = ("Analyserar, designar och utvecklar IT-system eller delar av system. Utformar och "
       "utvecklar lösningar för programvara, applikationer, system och databaser. ") * 4
RUNS = [("kblab", "float32"), ("harrier", "float32"), ("harrier", "bfloat16")]


class Result(BaseModel):
    model: str
    dtype: str
    dim: int
    max_seq: int
    load_s: float
    peak_gb: float
    short_ms: tuple[int, int]  # p50, p95
    ad_ms: tuple[int, int]
    doc_ms: int


def _child(name: str, dtype: str) -> None:
    import resource
    import time

    import torch
    from sentence_transformers import SentenceTransformer

    from lonekrav.core.embeddings import SPECS

    spec = SPECS[name]
    t = time.perf_counter()
    m = SentenceTransformer(spec.hf_id, device="cpu",
                            model_kwargs={"torch_dtype": getattr(torch, dtype)})
    load = time.perf_counter() - t
    kw = {"prompt_name": spec.query_prompt_name} if spec.query_prompt_name else {}

    def pct(texts, n):
        m.encode(texts, **kw)
        ts = []
        for _ in range(n):
            t = time.perf_counter()
            m.encode(texts, **kw)
            ts.append((time.perf_counter() - t) * 1000)
        ts.sort()
        return round(ts[len(ts) // 2]), round(ts[max(0, int(len(ts) * 0.95) - 1)])

    short, ad = pct([SHORT], 30), pct([AD], 10)
    t = time.perf_counter()
    m.encode([DOC] * 64, batch_size=32)
    doc = round((time.perf_counter() - t) * 1000 / 64)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_gb = peak / 1e9 if sys.platform == "darwin" else peak / 1e6  # bytes on macOS, KiB on Linux
    print(Result(model=spec.hf_id, dtype=dtype, dim=m.get_sentence_embedding_dimension(),
                 max_seq=m.max_seq_length, load_s=load, peak_gb=round(peak_gb, 2),
                 short_ms=short, ad_ms=ad, doc_ms=doc).model_dump_json())


def render(results: list[Result], machine: str, date: str) -> str:
    lines = [
        "# Embedding model measurements", "",
        f"Measured {date} on {machine}, CPU only, by `lonekrav-etl measure-models`. Short query is",
        f'"{SHORT}"; ad is a 600-word English job ad; documents are about 80-word Swedish',
        "descriptions in batches of 32. Peak is the model process's max RSS.", "",
        ("| Model | dtype | Dim | Max seq | Load | Peak RSS | Short query p50 / p95 "
        "| Ad p50 / p95 | Per document |"),
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(f"| {r.model} | {r.dtype} | {r.dim} | {r.max_seq} | {r.load_s:.0f} s | "
                     f"{r.peak_gb:.2f} GB | {r.short_ms[0]} / {r.short_ms[1]} ms | "
                     f"{r.ad_ms[0]} / {r.ad_ms[1]} ms | {r.doc_ms} ms |")
    lines += ["", "Harrier is loaded in float32: its bfloat16 checkpoint is far slower on CPU.",
              "The container memory cap is 5 GB (4 GB from 2026-10-20; raised on 2026-10-22 after measuring the container, references/container-memory.md).", ""]
    return "\n".join(lines)


def measure(out: Path = OUT) -> None:
    results = []
    for name, dtype in RUNS:
        print(f"measure {name} {dtype} ...", flush=True)
        code = f"from lonekrav.etl.measure import _child; _child({name!r}, {dtype!r})"
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                              check=True)
        results.append(Result.model_validate(json.loads(proc.stdout.strip().splitlines()[-1])))
    machine = platform.processor() or platform.machine()
    try:
        machine = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True,
                                 text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        pass
    out.write_text(render(results, machine, dt.date.today().isoformat()))
    print(f"wrote {out}")
