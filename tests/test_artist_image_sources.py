from __future__ import annotations

from downtify import artist_image_sources as sources


def test_fetch_online_artist_image_uses_first_successful_source(monkeypatch):
    calls: list[str] = []

    def fake_spotify(name: str):
        calls.append('spotify')
        return None, ''

    def fake_apple(name: str):
        calls.append('apple')
        return b'apple-image', 'Apple Music'

    def fake_discogs(name: str, *, discogs_token: str = ''):
        calls.append('discogs')
        return b'discogs-image', 'Discogs'

    monkeypatch.setattr(sources, 'fetch_spotify_artist_image', fake_spotify)
    monkeypatch.setattr(sources, 'fetch_apple_music_artist_image', fake_apple)
    monkeypatch.setattr(sources, 'fetch_discogs_artist_image', fake_discogs)
    sources._NAME_IMAGE_CACHE.clear()

    data, source = sources.fetch_online_artist_image('Philadelphia Orchestra')

    assert data == b'apple-image'
    assert source == 'Apple Music'
    assert calls == ['apple']


def test_fetch_discogs_artist_image_downloads_primary_image(monkeypatch):
    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        @staticmethod
        def raise_for_status():
            return None

        def json(self):
            return self._payload

    def fake_get(url, headers=None, params=None, timeout=0):
        if url.endswith('/search'):
            return FakeResponse(
                {
                    'results': [
                        {
                            'id': 27519,
                            'title': 'The Philadelphia Orchestra',
                        }
                    ]
                }
            )
        if url.endswith('/artists/27519'):
            return FakeResponse(
                {
                    'images': [
                        {
                            'type': 'primary',
                            'uri': 'https://example.test/artist.jpg',
                        }
                    ]
                }
            )
        raise AssertionError(url)

    monkeypatch.setattr(sources.requests, 'get', fake_get)
    monkeypatch.setattr(
        sources,
        '_download_image',
        lambda url: b'image-bytes' if url == 'https://example.test/artist.jpg' else None,
    )
    sources._NAME_IMAGE_CACHE.clear()

    data, source = sources.fetch_discogs_artist_image('Philadelphia Orchestra')

    assert data == b'image-bytes'
    assert source == 'Discogs'


def test_fetch_apple_music_artist_image_scrapes_og_image(monkeypatch):
    class FakeResponse:
        def __init__(self, *, text: str = '', payload: dict | None = None):
            self.text = text
            self._payload = payload or {}

        @staticmethod
        def raise_for_status():
            return None

        def json(self):
            return self._payload

    def fake_get(url, headers=None, params=None, timeout=0):
        if 'itunes.apple.com/search' in url:
            return FakeResponse(
                payload={
                    'results': [
                        {
                            'artistName': 'The Philadelphia Orchestra',
                            'artistLinkUrl': 'https://music.apple.com/us/artist/test/1',
                        }
                    ]
                }
            )
        if 'music.apple.com' in url:
            return FakeResponse(
                text=(
                    '<meta property="og:image" '
                    'content="https://is1-ssl.mzstatic.com/image/thumb/100x100bb.jpg">'
                )
            )
        raise AssertionError(url)

    monkeypatch.setattr(sources.requests, 'get', fake_get)
    monkeypatch.setattr(
        sources,
        '_download_image',
        lambda url: b'apple-image' if '600x600bb.jpg' in url else None,
    )
    sources._NAME_IMAGE_CACHE.clear()

    data, source = sources.fetch_apple_music_artist_image('Philadelphia Orchestra')

    assert data == b'apple-image'
    assert source == 'Apple Music'


def test_fetch_spotify_artist_image_uses_search_results(monkeypatch):
    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload
            self.status_code = 200

        @staticmethod
        def raise_for_status():
            return None

        def json(self):
            return self._payload

    def fake_get(url, headers=None, params=None, timeout=0):
        if url.endswith('/get_access_token'):
            return FakeResponse(
                {
                    'accessToken': 'token',
                    'accessTokenExpirationTimestampMs': 999999999999,
                }
            )
        if url.startswith('https://api.spotify.com/v1/search'):
            return FakeResponse(
                {
                    'artists': {
                        'items': [
                            {
                                'name': 'The Philadelphia Orchestra',
                                'images': [
                                    {'url': 'https://example.test/small.jpg', 'width': 64},
                                    {'url': 'https://example.test/large.jpg', 'width': 640},
                                ],
                            }
                        ]
                    }
                }
            )
        raise AssertionError(url)

    monkeypatch.setattr(sources.requests, 'get', fake_get)
    monkeypatch.setattr(
        sources,
        '_download_image',
        lambda url: b'spotify-image' if url.endswith('/large.jpg') else None,
    )
    sources._SPOTIFY_TOKEN.clear()
    sources._NAME_IMAGE_CACHE.clear()

    data, source = sources.fetch_spotify_artist_image('Philadelphia Orchestra')

    assert data == b'spotify-image'
    assert source == 'Spotify'


def test_spotify_access_token_marks_blocked_on_forbidden(monkeypatch):
    class FakeResponse:
        status_code = 403

        @staticmethod
        def raise_for_status():
            return None

    monkeypatch.setattr(sources.requests, 'get', lambda *args, **kwargs: FakeResponse())
    sources._SPOTIFY_TOKEN.clear()

    assert sources._spotify_access_token() == ''
    assert sources._spotify_access_token() == ''
    assert sources._SPOTIFY_TOKEN.get('blocked') is True
