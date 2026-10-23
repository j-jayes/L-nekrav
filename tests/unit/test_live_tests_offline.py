"""Collecting the live JobSearch test must not touch the network (FR-007, Copilot on PR #5)."""

import importlib.util
from pathlib import Path

import httpx


def test_importing_the_live_market_test_makes_no_request(monkeypatch):
    def no_network(*a, **kw):
        raise AssertionError("network call at import")

    monkeypatch.setattr(httpx, "get", no_network)
    path = Path(__file__).parents[1] / "integration" / "test_market_live.py"
    spec = importlib.util.spec_from_file_location("market_live_probe", path)
    spec.loader.exec_module(importlib.util.module_from_spec(spec))
