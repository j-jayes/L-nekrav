import subprocess
import sys


def test_torch_works_after_opening_the_store(tmp_path):
    """Found by hand (exit 139): faiss (inside Milvus Lite) and torch each ship libomp on macOS.
    If faiss loads first, the first torch op segfaults. Importing the store must be safe."""
    code = (
        "import pathlib; from lonekrav.core.store import Store; "
        f"s = Store(pathlib.Path({str(tmp_path)!r}) / 'x.db', dims={{}}); s.create(); "
        "import torch; a = torch.randn(512, 512); print(float((a @ a).abs().sum()) > 0)"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120,
                         check=False)
    assert out.returncode == 0, f"exit {out.returncode}: {out.stderr[-500:]}"
    assert out.stdout.strip().endswith("True")
