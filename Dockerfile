# arm64 is the default container target (ADR 0005); python:*-slim publishes a
# native linux/arm64 image, so no emulation is needed on the Graviton host.
FROM python:3.14-slim

# Bring uv in for a standards-aligned install (no pip). The app has no runtime
# dependencies, so this only builds and installs the wkx_hello package.
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /bin/uv

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src

# Install into the system interpreter so `python3 -m wkx_hello.*` resolves with
# no activated venv (both the app CMD and the healthcheck rely on this).
RUN uv pip install --system --no-cache .

# Run unprivileged.
RUN useradd --system --no-create-home wkx
USER wkx

EXPOSE 8000
CMD ["python3", "-m", "wkx_hello.app"]
