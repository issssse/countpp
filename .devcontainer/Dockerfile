FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends jq ripgrep fd-find \
    && ln -sf /usr/bin/fdfind /usr/local/bin/fd \
    && python -m pip install --no-cache-dir uv ruff pyright \
    && rm -rf /var/lib/apt/lists/*
