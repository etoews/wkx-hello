# arm64 is the default container target (ADR 0005); python:*-slim publishes a
# native linux/arm64 image, so no emulation is needed on the Graviton host.

# Build stage: uv installs the wkx_hello package (no runtime dependencies) into
# an isolated prefix. uv and the build backend live only here, never in runtime.
FROM python:3.14-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /bin/uv
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN uv pip install --no-cache --target /install .

# Runtime stage: the standard library plus the app package, nothing else. The
# slim base ships pip/setuptools (and their transitive build tooling) whose
# known-fixable CVEs would trip the deploy scan gate, and a stdlib-only app
# needs none of them at runtime, so strip them before copying the app in.
FROM python:3.14-slim
RUN find /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14 \
      -maxdepth 1 \( -name 'pip*' -o -name 'setuptools*' -o -name 'pkg_resources*' \
      -o -name 'wheel*' -o -name 'msgpack*' -o -name '_distutils_hack*' \
      -o -name 'ensurepip' \) -exec rm -rf {} + 2>/dev/null || true
COPY --from=build /install /usr/local/lib/python3.14/site-packages/

# Run unprivileged.
RUN useradd --system --no-create-home wkx
USER wkx

EXPOSE 8000
CMD ["python3", "-m", "wkx_hello.app"]
