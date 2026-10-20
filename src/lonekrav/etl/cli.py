"""`lonekrav-etl`: fetch | build | index | benchmark | measure-models (contracts/cli.md)."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable

SOURCES = ("scb_files", "scb_pxweb", "jobtech", "ilo", "esco", "mis2012")


def _todo(args: argparse.Namespace) -> None:
    raise NotImplementedError(f"'{args.command}' is not implemented yet")


COMMANDS: dict[str, Callable[[argparse.Namespace], None]] = {
    "fetch": _todo,
    "build": _todo,
    "index": _todo,
    "benchmark": _todo,
    "measure-models": _todo,
}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="lonekrav-etl", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    f = sub.add_parser("fetch", help="download raw sources to data/raw/")
    f.add_argument("--only", nargs="+", metavar="SOURCE", help=f"subset of: {', '.join(SOURCES)}")
    f.add_argument("--force", action="store_true", help="re-download cached files")
    sub.add_parser("build", help="data/raw/ -> data/processed/")
    i = sub.add_parser("index", help="data/processed/ -> Milvus Lite index")
    i.add_argument("--models", default="kblab,harrier")
    i.add_argument("--db", default=None, help="index file (MILVUS_URI overrides)")
    b = sub.add_parser("benchmark", help="cross-lingual benchmark -> benchmark_results.json")
    b.add_argument("--db", default=None)
    sub.add_parser("measure-models", help="model latency and memory -> references/")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "fetch":
        for s in args.only or ():
            if s not in SOURCES:
                print(f"error: unknown source '{s}' (choose from {', '.join(SOURCES)})",
                      file=sys.stderr)
                return 1
    try:
        COMMANDS[args.command](args)
    except Exception as e:  # noqa: BLE001 - one-line cause for the user; traceback adds nothing
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
