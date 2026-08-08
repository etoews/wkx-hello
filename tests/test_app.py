"""HTTP-seam tests: a real server on an ephemeral port, real requests.

Every test drives the app through a running ThreadingHTTPServer bound to port 0,
so the request path (routing, headers, escaping) is exercised end to end rather
than by calling handler methods directly.
"""

import http.client
import threading
import urllib.request
from collections.abc import Iterator
from http.server import ThreadingHTTPServer

import pytest

from wkx_hello.app import Handler


@pytest.fixture
def base_url() -> Iterator[str]:
    """Start the real app server on an ephemeral port and yield its base URL."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_get_returns_200_html_with_default_message(base_url: str) -> None:
    """GET / is 200, text/html; charset=utf-8, and carries the default MESSAGE."""
    with urllib.request.urlopen(base_url + "/") as response:
        status = response.status
        content_type = response.headers["Content-Type"]
        body = response.read()

    assert status == 200
    assert content_type == "text/html; charset=utf-8"
    assert b"hello, wing kong exchange" in body


def test_head_matches_get_headers_with_empty_body(base_url: str) -> None:
    """HEAD returns 200 with GET's headers (incl. Content-Length) and no body."""
    host = base_url.removeprefix("http://")

    get_conn = http.client.HTTPConnection(host)
    get_conn.request("GET", "/")
    get_response = get_conn.getresponse()
    get_body = get_response.read()
    get_type = get_response.getheader("Content-Type")
    get_length = get_response.getheader("Content-Length")
    get_conn.close()

    head_conn = http.client.HTTPConnection(host)
    head_conn.request("HEAD", "/")
    head_response = head_conn.getresponse()
    head_body = head_response.read()
    head_type = head_response.getheader("Content-Type")
    head_length = head_response.getheader("Content-Length")
    head_conn.close()

    assert head_response.status == 200
    assert head_body == b""
    assert head_type == get_type
    assert head_length == get_length
    assert head_length == str(len(get_body))


def test_message_markup_is_escaped(base_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """A MESSAGE containing markup is HTML-escaped in the page, never raw."""
    monkeypatch.setenv("MESSAGE", "<script>alert(1)</script>")

    with urllib.request.urlopen(base_url + "/") as response:
        body = response.read().decode()

    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in body
    assert "<script>" not in body


def test_message_env_var_changes_page(base_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Setting the MESSAGE environment variable changes the rendered page."""
    monkeypatch.setenv("MESSAGE", "kia ora")

    with urllib.request.urlopen(base_url + "/") as response:
        body = response.read().decode()

    assert "kia ora" in body
