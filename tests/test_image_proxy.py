from unittest.mock import MagicMock

import pytest

from downtify import image_proxy


@pytest.mark.parametrize(
    'url',
    [
        'https://i.scdn.co/image/ab67616d0000b273example',
        'https://lh3.googleusercontent.com/photo-example=w600-h600',
        'https://i.ytimg.com/vi/abc123/hqdefault.jpg',
    ],
)
def test_is_allowed_image_url_accepts_music_cdns(url):
    assert image_proxy.is_allowed_image_url(url)


@pytest.mark.parametrize(
    'url',
    [
        '',
        'ftp://i.scdn.co/image/x',
        'https://evil.example/art.jpg',
        'http://127.0.0.1/cover.jpg',
        'http://localhost/cover.jpg',
    ],
)
def test_is_allowed_image_url_rejects_invalid(url):
    assert not image_proxy.is_allowed_image_url(url)


def test_fetch_remote_image_returns_bytes(monkeypatch):
    response = MagicMock()
    response.headers = {'Content-Type': 'image/jpeg; charset=utf-8'}
    response.content = b'jpeg-bytes'
    response.raise_for_status = MagicMock()
    monkeypatch.setattr(image_proxy.requests, 'get', lambda *args, **kwargs: response)

    data, mime = image_proxy.fetch_remote_image(
        'https://i.scdn.co/image/ab67616d0000b273example'
    )

    assert data == b'jpeg-bytes'
    assert mime == 'image/jpeg'
