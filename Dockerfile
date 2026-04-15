# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:0.11.6-python3.13-trixie@sha256:b3c543b6c4f23a5f2df22866bd7857e5d304b67a564f4feab6ac22044dde719b AS uv_source
FROM tianon/gosu:1.19-trixie@sha256:3b176695959c71e123eb390d427efc665eeb561b1540e82679c15e992006b8b9 AS gosu_source
FROM debian:13.4

# Disable Python stdout buffering to ensure logs are printed immediately
ENV PYTHONUNBUFFERED=1

# Store Playwright browsers outside the volume mount so the build-time
# install survives the /opt/data volume overlay at runtime.
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/hermes/.playwright

# Keep the build isolated from host- or network-injected proxy settings.
ENV HTTP_PROXY= \
    HTTPS_PROXY= \
    http_proxy= \
    https_proxy= \
    NO_PROXY= \
    no_proxy=

COPY docker/certs/sophos-xg-home.crt /tmp/sophos-xg-home.crt

# Neutralize hidden APT proxy settings from the host/runtime during image build.
RUN printf 'Acquire::http::Proxy "false";\nAcquire::https::Proxy "false";\n' > /etc/apt/apt.conf.d/99no-proxy

# Prefer HTTPS Debian mirrors so local firewalls/proxies do not interfere with HTTP package fetches.
RUN sed -i 's|http://deb.debian.org/debian|https://deb.debian.org/debian|g' /etc/apt/sources.list.d/*.sources

# Bootstrap APT through networks that intercept TLS until the Sophos CA is trusted system-wide.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    printf 'Acquire::https::Verify-Peer "false";\nAcquire::https::Verify-Host "false";\n' > /etc/apt/apt.conf.d/99bootstrap-insecure && \
    apt-get -o Acquire::http::Proxy=false -o Acquire::https::Proxy=false update && \
    apt-get -o Acquire::http::Proxy=false -o Acquire::https::Proxy=false install -y --no-install-recommends \
        ca-certificates build-essential nodejs npm python3 ripgrep ffmpeg gcc python3-dev libffi-dev procps git \
        curl wget unzip xz-utils jq file less && \
    install -Dm644 /tmp/sophos-xg-home.crt /usr/local/share/ca-certificates/sophos-xg-home.crt && \
    update-ca-certificates && \
    rm -f /etc/apt/apt.conf.d/99bootstrap-insecure /tmp/sophos-xg-home.crt && \
    rm -rf /var/lib/apt/lists/*

# Non-root user for runtime; UID can be overridden via HERMES_UID at runtime
RUN useradd -u 10000 -m -d /opt/data hermes

COPY --chmod=0755 --from=gosu_source /gosu /usr/local/bin/
COPY --chmod=0755 --from=uv_source /usr/local/bin/uv /usr/local/bin/uvx /usr/local/bin/

WORKDIR /opt/hermes

COPY pyproject.toml uv.lock README.md package.json package-lock.json /opt/hermes/
COPY scripts/whatsapp-bridge/package.json scripts/whatsapp-bridge/package-lock.json /opt/hermes/scripts/whatsapp-bridge/

# Resolve JS dependencies before copying the full source tree so code-only changes
# can still reuse the heavier npm/playwright cache layers.
RUN --mount=type=cache,target=/root/.npm,sharing=locked \
    npm install --prefer-offline --no-audit && \
    npx playwright install --with-deps chromium --only-shell && \
    cd /opt/hermes/scripts/whatsapp-bridge && \
    npm install --prefer-offline --no-audit && \
    npm cache clean --force

COPY . /opt/hermes

# Hand ownership to hermes user, then install Python deps in a virtualenv.
RUN chown -R hermes:hermes /opt/hermes
USER hermes

RUN --mount=type=cache,target=/home/hermes/.cache/uv,sharing=locked \
    uv venv && \
    uv pip install --no-cache-dir -e ".[all]"

USER root
RUN chmod +x /opt/hermes/docker/entrypoint.sh

ENV HERMES_HOME=/opt/data
VOLUME [ "/opt/data" ]
ENTRYPOINT [ "/opt/hermes/docker/entrypoint.sh" ]
