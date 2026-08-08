# wkx-hello

The wkx reference app and platform smoke test: it proves the request path
browser to Cloudflare to Caddy to container. It is a dependency-free HTTP server
that answers every GET with a single, HTML-escaped `MESSAGE`, and it becomes the
ancestor of the M8 reference project.

Extracted from `wkx-platform/hello/` at M6 and crossed over from stdlib-only to
the uv-packaged Python shape (see the platform's `docs/standards/python.md`).

## What it does

- `GET /` returns `200` with `text/html; charset=utf-8` and `MESSAGE` in an
  `<h1>`, HTML-escaped so an operator-supplied value is never treated as markup.
- `HEAD /` returns `200` with the same headers as `GET` (including
  `Content-Length`) and no body.
- `MESSAGE` is read from the environment on each request (default:
  `hello, wing kong exchange`). On the platform it is driven by SSM at
  `/wkx/hello/<env>/MESSAGE`, rendered into the container's env-file at deploy
  time, so changing the page is a redeploy, not a code change.

## Layout

- `src/wkx_hello/app.py`: the HTTP server on port `8000`.
- `src/wkx_hello/healthcheck.py`: a stdlib probe (`python3 -m wkx_hello.healthcheck`)
  the container healthcheck runs, because the slim image ships no curl.
- `tests/`: pytest at the HTTP seam, driving a real server on an ephemeral port.
- `Dockerfile`: native `linux/arm64` (ADR 0005) `python:3.14-slim` base.
- `compose.yml` and `compose.cloud.yml`: the deploy stack and its awslogs overlay
  (the log group is parameterised by env).
- `caddy.snippet`: the single host block Caddy renders per env (ADR 0018).

## Develop

```
uv sync            # create the venv and install deps (adds --locked in CI)
uv run ruff check
uv run ruff format --check
uv run ty check
uv run pytest
```

Run the server locally with `uv run wkx-hello` (or `MESSAGE="kia ora" uv run
wkx-hello`), then open http://localhost:8000/.

## CI

`.github/workflows/ci.yml` runs on every pull request: the gate block above, then
a native ARM container build (build only, no push) on GitHub's stable ARM runner.
The build sets `provenance: false` and `sbom: false` so ECR receives a plain,
scannable manifest (ADR 0025). ECR push, the deploy bundle, and the deploy itself
arrive with the deploy workflow in a later M6 change.
