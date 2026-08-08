"""Container healthcheck: succeed only when the app answers 200 on /.

The slim runtime image ships no curl, so the compose healthcheck runs this with
`python3 -m wkx_hello.healthcheck`. It uses stdlib urllib and exits 0 on HTTP 200,
non-zero otherwise, which is the contract Docker's healthcheck expects.
"""

import sys
import urllib.request

URL = "http://localhost:8000/"
TIMEOUT_SECONDS = 3.0


def check(url: str = URL, timeout: float = TIMEOUT_SECONDS) -> int:
    """Probe url once and return a process exit code.

    Args:
        url: The endpoint to probe.
        timeout: Per-request timeout in seconds.

    Returns:
        0 if the endpoint answered HTTP 200, 1 otherwise (including any
        connection error or non-200 status).
    """
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return 0 if response.status == 200 else 1
    except OSError:
        # URLError, HTTPError, and socket timeouts are all OSError subclasses.
        return 1


def main() -> int:
    """Probe the default URL and return its exit code."""
    return check()


if __name__ == "__main__":
    sys.exit(main())
