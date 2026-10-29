# 하네스 트랙 공통 이미지: Python 3.12 + Node 22 + pytest, 하네스 4개와 의존성
FROM node:22-bookworm-slim AS node
FROM python:3.12-slim-bookworm
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
 && apt-get update && apt-get install -y --no-install-recommends git ripgrep ca-certificates procps \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir pytest uv \
 && npm install -g pnpm@11.3.0
ENV UV_PYTHON_DOWNLOADS=never
WORKDIR /opt/h
COPY claude-agent-sdk/pyproject.toml claude-agent-sdk/uv.lock claude-agent-sdk/
COPY deepagents/pyproject.toml deepagents/uv.lock deepagents/
RUN uv sync --frozen --project claude-agent-sdk && uv sync --frozen --project deepagents
COPY pi/package.json pi/pnpm-lock.yaml pi/pnpm-workspace.yaml pi/
COPY flue/package.json flue/pnpm-lock.yaml flue/pnpm-workspace.yaml flue/
RUN cd pi && pnpm install --frozen-lockfile && cd ../flue && pnpm install --frozen-lockfile
COPY claude-agent-sdk/*.py claude-agent-sdk/
COPY deepagents/*.py deepagents/
COPY pi/*.ts pi/
COPY flue/*.ts flue/
