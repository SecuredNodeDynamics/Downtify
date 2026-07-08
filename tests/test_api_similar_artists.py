from downtify import api


class FakeYTMusic:
    def search(self, query, filter, limit):
        assert query == 'Oasis'
        assert filter == 'artists'
        assert limit == 5
        return [
            {'artist': 'Oasis Tribute', 'browseId': 'tribute'},
            {'artist': 'Oasis', 'browseId': 'oasis'},
        ]

    def get_artist(self, browse_id):
        assert browse_id == 'oasis'
        return {
            'related': {
                'results': [
                    {
                        'artist': 'Blur',
                        'browseId': 'blur',
                        'thumbnails': [
                            {'url': 'https://i.ytimg.com/small.jpg', 'width': 60},
                            {
                                'url': 'https://i.ytimg.com/large.jpg',
                                'width': 240,
                                'height': 240,
                            },
                        ],
                    },
                    {'artist': 'blur', 'browseId': 'duplicate'},
                    {'artist': 'Oasis', 'browseId': 'self'},
                    {'title': 'Pulp', 'browseId': 'pulp'},
                ]
            }
        }


def test_similar_artists_match_dedupe_and_proxy_images(monkeypatch):
    api._SIMILAR_ARTISTS_CACHE.clear()
    monkeypatch.setattr(api.providers, '_ytm', lambda: FakeYTMusic())
    monkeypatch.setattr(
        api.artist_image_options,
        '_spotify_artist_items',
        lambda *_args, **_kwargs: [
            {
                'id': 'suede',
                'name': 'Suede',
                'images': [{'url': 'https://i.scdn.co/suede.jpg', 'width': 300}],
            },
            {
                'id': 'blur-spotify',
                'name': 'Blur',
                'images': [{'url': 'https://i.scdn.co/blur.jpg', 'width': 300}],
            },
        ],
    )

    result = api.get_similar_artists('Oasis', 8)

    assert [artist['name'] for artist in result['artists']] == [
        'Suede',
        'Blur',
        'Pulp',
    ]
    assert result['artists'][0]['source'] == 'spotify'
    assert result['artists'][1]['source'] == 'youtube_music'
    assert result['artists'][1]['browse_id'] == 'blur'
    assert result['artists'][0]['image_url'] == 'https://i.scdn.co/suede.jpg'
    assert result['artists'][1]['image_url'] == 'https://i.ytimg.com/large.jpg'


def test_similar_artists_failure_returns_empty(monkeypatch):
    api._SIMILAR_ARTISTS_CACHE.clear()

    def fail():
        raise RuntimeError('offline')

    monkeypatch.setattr(api.providers, '_ytm', fail)
    monkeypatch.setattr(
        api.artist_image_options,
        '_spotify_artist_items',
        lambda *_args, **_kwargs: [],
    )

    assert api.get_similar_artists('Oasis', 8) == {
        'artist': 'Oasis',
        'artists': [],
    }
