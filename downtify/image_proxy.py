"""Fetch remote album-art URLs for clients that cannot load CDNs directly."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

import requests

_IMAGE_PROXY_UA = 'Downtify/1.0'

_ALLOWED_IMAGE_HOST_SUFFIXES = (
    'scdn.co',
    'spotifycdn.com',
    'googleusercontent.com',
    'ggpht.com',
    'ytimg.com',
    'mzstatic.com',
)


def _hostname_allowed(host: str) -> bool:
    normalized = str(host or '').lower().rstrip('.')
    if not normalized:
        return False
    return any(
        normalized == suffix or normalized.endswith(f'.{suffix}')
        for suffix in _ALLOWED_IMAGE_HOST_SUFFIXES
    )


def _resolve_host_ips(host: str) -> list[str]:
    try:
        infos = socket.getaddrinfo(host, None)
    except (OSError, UnicodeError, ValueError):
        # Name resolution can fail or behave unexpectedly on some runtimes
        # (e.g. Android). The host allow-list above already restricts targets to
        # trusted CDNs, so an inconclusive lookup must not raise.
        return []
    addresses: list[str] = []
    for info in infos:
        sockaddr = info[4]
        if sockaddr:
            addresses.append(str(sockaddr[0]))
    return addresses


def _ip_is_public(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def is_allowed_image_url(url: str) -> bool:
    parsed = urlparse(str(url or '').strip())
    if parsed.scheme not in {'http', 'https'}:
        return False
    host = parsed.hostname or ''
    if not _hostname_allowed(host):
        return False
    if host in {'localhost', '127.0.0.1', '::1', '0.0.0.0'}:
        return False

    if host.replace('.', '').isdigit():
        return _ip_is_public(host)

    for address in _resolve_host_ips(host):
        if not _ip_is_public(address):
            return False
    return True


def fetch_remote_image(url: str) -> tuple[bytes, str]:
    response = requests.get(
        url,
        timeout=12,
        headers={
            'User-Agent': _IMAGE_PROXY_UA,
            'Accept': 'image/*,*/*',
        },
    )
    response.raise_for_status()
    content_type = response.headers.get('Content-Type', 'image/jpeg').split(';')[0].strip()
    if not content_type.startswith('image/'):
        raise ValueError('Remote response is not an image')
    return response.content, content_type
