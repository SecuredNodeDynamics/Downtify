from __future__ import annotations

from downtify import artist_image_options as options


def test_collect_artist_image_options_includes_jellyfin_and_sources(
    monkeypatch,
):
    monkeypatch.setattr(
        options,
        'list_spotify_artist_image_options',
        lambda *_args, **_kwargs: [
            {
                'id': 'spotify:abc',
                'source': 'Spotify',
                'label': 'Jane Murdoch',
                'subtitle': '95% name match',
                'image_url': 'https://i.scdn.co/image/abc.jpg',
                'jellyfin_artist_id': '',
            }
        ],
    )
    monkeypatch.setattr(
        options,
        'list_discogs_artist_image_options',
        lambda *_args, **_kwargs: [
            {
                'id': 'discogs:123',
                'source': 'Discogs',
                'label': 'Jane Murdoch',
                'subtitle': '95% name match',
                'image_url': 'https://img.discogs.com/artist.jpg',
                'jellyfin_artist_id': '',
            }
        ],
    )
    monkeypatch.setattr(
        options,
        'list_musicbrainz_artist_image_options',
        lambda *_args, **_kwargs: [
            {
                'id': 'musicbrainz:mbid:musicbrainz',
                'source': 'MusicBrainz',
                'label': 'Jane Murdoch',
                'subtitle': '95% name match',
                'image_url': 'https://commons.wikimedia.org/wiki/Special:FilePath/test.jpg',
                'jellyfin_artist_id': '',
            }
        ],
    )

    result = options.collect_artist_image_options(
        'Jane Murdoch',
        jellyfin_artist_id='jf-1',
    )

    assert result[0]['source'] == 'Jellyfin'
    assert result[0]['jellyfin_artist_id'] == 'jf-1'
    assert {item['source'] for item in result[1:]} == {
        'Spotify',
        'Discogs',
        'MusicBrainz',
    }


def test_list_spotify_artist_image_options_filters_low_matches(monkeypatch):
    monkeypatch.setattr(
        options.artist_image_sources,
        '_spotify_access_token',
        lambda: 'token',
    )

    class FakeResponse:
        status_code = 200

        @staticmethod
        def raise_for_status():
            return None

        @staticmethod
        def json():
            return {
                'artists': {
                    'items': [
                        {
                            'id': 'good',
                            'name': 'Jane Murdoch',
                            'images': [
                                {'url': 'https://i.scdn.co/image/good.jpg', 'width': 640}
                            ],
                        },
                        {
                            'id': 'bad',
                            'name': 'Different Artist',
                            'images': [
                                {'url': 'https://i.scdn.co/image/bad.jpg', 'width': 640}
                            ],
                        },
                    ]
                }
            }

    monkeypatch.setattr(options.requests, 'get', lambda *args, **kwargs: FakeResponse())

    result = options.list_spotify_artist_image_options('Jane Murdoch')

    assert len(result) == 1
    assert result[0]['id'] == 'spotify:good'
    assert result[0]['image_url'] == 'https://i.scdn.co/image/good.jpg'
