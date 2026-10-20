import hashlib
import json

import httpx
import pytest

from lonekrav.etl.http import FetchError, cached_get, read_meta


def client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_download_writes_file_and_meta(tmp_path):
    dest = tmp_path / "scb" / "a.xlsx"
    c = client(lambda req: httpx.Response(200, content=b"abc"))
    path = cached_get("scb_files", "https://example.org/a.xlsx", dest, client=c)
    assert path.read_bytes() == b"abc"
    meta = json.loads((tmp_path / "scb" / "a.xlsx.meta.json").read_text())
    assert meta["url"] == "https://example.org/a.xlsx"
    assert meta["sha256"] == hashlib.sha256(b"abc").hexdigest()
    assert read_meta(dest).fetched_at.tzinfo is not None


def test_cached_file_is_reused_without_force(tmp_path):
    dest = tmp_path / "a.json"
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(200, content=b"{}")

    cached_get("jobtech", "https://example.org/a", dest, client=client(handler))
    cached_get("jobtech", "https://example.org/a", dest, client=client(handler))
    assert len(calls) == 1
    cached_get("jobtech", "https://example.org/a", dest, client=client(handler), force=True)
    assert len(calls) == 2


@pytest.mark.parametrize(
    "handler",
    [
        lambda req: httpx.Response(500, content=b"boom"),
        lambda req: (_ for _ in ()).throw(httpx.ConnectError("refused", request=req)),
    ],
    ids=["http-500", "connection-error"],
)
def test_failed_download_names_source_and_url_and_keeps_old_file(tmp_path, handler):
    dest = tmp_path / "a.json"
    cached_get("scb_pxweb", "https://example.org/a", dest,
               client=client(lambda r: httpx.Response(200, content=b"good")))
    with pytest.raises(FetchError, match=r"scb_pxweb.*https://example.org/a"):
        cached_get("scb_pxweb", "https://example.org/a", dest, client=client(handler), force=True)
    assert dest.read_bytes() == b"good"
    assert not list(tmp_path.glob("*.tmp"))


def test_validate_rejects_bad_payload_without_replacing_cache(tmp_path):
    dest = tmp_path / "a.json"
    cached_get("esco", "https://example.org/a", dest,
               client=client(lambda r: httpx.Response(200, content=b"good")))

    def must_be_json(data: bytes):
        json.loads(data)

    with pytest.raises(FetchError, match="esco"):
        cached_get("esco", "https://example.org/a", dest, force=True, validate=must_be_json,
                   client=client(lambda r: httpx.Response(200, content=b"<html>")))
    assert dest.read_bytes() == b"good"
