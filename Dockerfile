FROM python:3.13-alpine AS builder

WORKDIR /build

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir --root-user-action ignore -r requirements.txt

FROM node:22-alpine AS frontend-builder

WORKDIR /build/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend ./
RUN npm run build

FROM python:3.13-alpine

LABEL maintainer="SecuredNodeDynamics"
LABEL version="2.10.83"
LABEL description="Self-hosted Spotify downloader"

LABEL org.opencontainers.image.title="Downtify" \
      org.opencontainers.image.description="Download your Spotify playlists and songs along with album art and metadata in a self-hosted way via Docker." \
      org.opencontainers.image.version="2.10.83" \
      org.opencontainers.image.authors="SecuredNodeDynamics" \
      org.opencontainers.image.url="https://github.com/SecuredNodeDynamics/Downtify" \
      org.opencontainers.image.source="https://github.com/SecuredNodeDynamics/Downtify" \
      org.opencontainers.image.licenses="GPL-3.0" \
      org.opencontainers.image.documentation="https://github.com/SecuredNodeDynamics/Downtify#readme" \
      org.opencontainers.image.vendor="SecuredNodeDynamics" \
      org.opencontainers.image.base.name="python:3.13-alpine"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHON_COLORS=0 \
    DOWNTIFY_LOG_LEVEL=info \
    DOWNTIFY_PORT=8000 \
    UID=1000 \
    GID=1000 \
    UMASK=022

WORKDIR /downtify

RUN apk add --no-cache \
    docker-cli \
    ffmpeg \
    shadow \
    su-exec \
    tini

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY main.py entrypoint.sh ./
COPY downtify ./downtify
COPY --from=frontend-builder /build/frontend/dist ./frontend/dist

RUN sed -i 's/\r$//g' entrypoint.sh && \
    chmod +x entrypoint.sh

ENV PATH="/home/downtify/.local/bin:${PATH}"

VOLUME /downloads
VOLUME /data

EXPOSE ${DOWNTIFY_PORT}

ENTRYPOINT ["/sbin/tini", "-g", "--", "./entrypoint.sh"]
