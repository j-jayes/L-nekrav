"""Copilot review on PR #1: a `fetch --force` that gets an HTML error page with HTTP 200 must not
replace a good cached workbook or PDF."""

import shutil

import httpx
import pytest

from lonekrav.etl import http, ilo, mis2012, scb_files
from lonekrav.etl.http import FetchError


@pytest.fixture
def html_200(monkeypatch):
    real = httpx.Client
    monkeypatch.setattr(http.httpx, "Client", lambda **kw: real(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, content=b"<html>busy</html>")),
        **kw))


def seed(src, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dest)
    return dest.read_bytes()


def test_scb_workbook_keeps_cache(fixtures, tmp_path, html_200):
    name = scb_files.FILES["structure"]
    good = seed(fixtures / "scb" / name, tmp_path / "scb" / name)
    with pytest.raises(FetchError, match="scb_files"):
        scb_files.fetch(tmp_path, force=True)
    assert (tmp_path / "scb" / name).read_bytes() == good


def test_ilo_workbook_keeps_cache(fixtures, tmp_path, html_200):
    good = seed(fixtures / "ilo/isco08_en.xlsx", tmp_path / "ilo/isco08_en.xlsx")
    with pytest.raises(FetchError, match="ilo"):
        ilo.fetch(tmp_path, force=True)
    assert (tmp_path / "ilo/isco08_en.xlsx").read_bytes() == good


def test_mis_pdf_keeps_cache(tmp_path, html_200):
    good = seed_pdf(tmp_path / "mis2012" / "ssyk2012.pdf")
    with pytest.raises(FetchError, match="mis2012"):
        mis2012.fetch(tmp_path, force=True)
    assert (tmp_path / "mis2012" / "ssyk2012.pdf").read_bytes() == good


def seed_pdf(dest):
    from pypdf import PdfWriter

    dest.parent.mkdir(parents=True, exist_ok=True)
    w = PdfWriter()
    w.add_blank_page(width=100, height=100)
    with dest.open("wb") as f:
        w.write(f)
    return dest.read_bytes()


def test_validators_accept_real_documents(fixtures, tmp_path):
    for key, name in scb_files.FILES.items():
        scb_files.validator(key)((fixtures / "scb" / name).read_bytes())
    ilo.validate((fixtures / "ilo/isco08_en.xlsx").read_bytes())
    mis2012.validate(seed_pdf(tmp_path / "x.pdf"))
