from downtify import artist_art
from downtify import artist_image_options as options
from downtify.metadata_repair import artist_search_names


def test_artist_search_names_splits_collaboration():
    names = artist_search_names('A$AP Rocky & French Montana')

    assert 'A$AP Rocky' in names
    assert 'French Montana' in names


def test_artist_search_names_strips_ensemble_suffix():
    names = artist_search_names('Darkest Hour Orchestra')

    assert 'Darkest Hour Orchestra' in names
    assert 'Darkest Hour' in names


def test_collect_artist_image_options_includes_jellyfin_and_sources(
    monkeypatch,
):
    monkeypatch.setattr(
        options,
        '_collect_for_search_name',
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

    result = options.collect_artist_image_options(
        'Jane Murdoch',
        jellyfin_artist_id='jf-1',
    )

    assert result[0]['source'] == 'Jellyfin'
    assert result[0]['jellyfin_artist_id'] == 'jf-1'
    assert result[1]['source'] == 'Spotify'


def test_list_musicbrainz_artist_image_options_uses_wikimedia_urls(
    monkeypatch,
):
    monkeypatch.setattr(
        options,
        '_musicbrainz_search_artists',
        lambda *_args, **_kwargs: [
            {'id': 'mbid-1', 'name': 'Andrew Bird'},
        ],
    )
    monkeypatch.setattr(
        options,
        '_wikimedia_artist_image_url',
        lambda mbid: f'https://commons.wikimedia.org/wiki/Special:FilePath/{mbid}.jpg',
    )

    result = options.list_musicbrainz_artist_image_options('Andrew Bird')

    assert len(result) == 1
    assert result[0]['id'] == 'musicbrainz:mbid-1'
    assert result[0]['image_url'].startswith('https://commons.wikimedia.org/')


def test_list_musicbrainz_artist_image_options_skips_missing_images(
    monkeypatch,
):
    monkeypatch.setattr(
        options,
        '_musicbrainz_search_artists',
        lambda *_args, **_kwargs: [
            {'id': 'mbid-1', 'name': 'Jane Murdoch'},
        ],
    )
    monkeypatch.setattr(
        options,
        '_wikimedia_artist_image_url',
        lambda *_args, **_kwargs: '',
    )

    result = options.list_musicbrainz_artist_image_options('Jane Murdoch')

    assert result == []


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


def test_list_youtube_music_artist_image_options(monkeypatch):
    monkeypatch.setattr(
        options.artist_image_sources,
        '_youtube_music_artist_items',
        lambda *_args, **_kwargs: [
            {
                'artist': 'Jane Murdoch',
                'browseId': 'browse-1',
                'thumbnails': [
                    {'url': 'https://yt3.googleusercontent.com/large', 'width': 600},
                ],
            }
        ],
    )

    result = options.list_youtube_music_artist_image_options('Jane Murdoch')

    assert len(result) == 1
    assert result[0]['source'] == 'YouTube Music'
    assert result[0]['id'] == 'youtube-music:browse-1'
