"""The wkx-hello HTTP server.

Responds 200 to every GET with MESSAGE from the environment, HTML-escaped so an
operator-supplied value can never be interpreted as markup. HEAD mirrors GET's
headers with no body. MESSAGE is the single config knob, driven by SSM at deploy
time (/wkx/hello/<env>/MESSAGE), rendered into the container's env-file, and read
at request time so a redeploy that changes it takes effect without a code change.
"""

import html
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MESSAGE = "hello, wing kong exchange"
PORT = 8000


def current_message() -> str:
    """Return the MESSAGE to display, from the environment or the default.

    Read on each request so a redeploy that changes /wkx/hello/<env>/MESSAGE
    (surfaced as the MESSAGE environment variable) takes effect immediately, and
    so tests can vary it by setting the environment variable.

    Returns:
        The raw, unescaped message. Callers must escape it before rendering.
    """
    return os.environ.get("MESSAGE", DEFAULT_MESSAGE)


def render_page(message: str) -> bytes:
    """Render the HTML page body for a message.

    Args:
        message: The operator-supplied message. It is HTML-escaped here so the
            page never interprets it as markup.

    Returns:
        The UTF-8 encoded HTML body.
    """
    return (
        f"<!doctype html>\n<title>hello · wkx</title>\n<h1>{html.escape(message)}</h1>\n".encode()
    )


class Handler(BaseHTTPRequestHandler):
    """Serve the hello page on GET, with a matching bodyless HEAD."""

    def _send_headers(self, body: bytes) -> None:
        """Send the 200 status line and the headers describing body.

        Args:
            body: The response body the headers describe. Content-Length is set
                from its length. HEAD sends these headers but not the body.
        """
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

    def do_GET(self) -> None:
        """Respond 200 with the rendered page."""
        body = render_page(current_message())
        self._send_headers(body)
        self.wfile.write(body)

    def do_HEAD(self) -> None:
        """Respond 200 with GET's headers and no body (fixes F-010)."""
        body = render_page(current_message())
        self._send_headers(body)

    def log_message(self, format: str, *args: Any) -> None:
        """Route request logs through stdlib logging so docker captures them."""
        logger.info('%s - "%s"', self.address_string(), format % args)


def main() -> None:
    """Configure logging and serve forever on PORT until interrupted."""
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    logger.info("serving on port %d", PORT)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
