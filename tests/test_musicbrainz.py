from __future__ import annotations

from downtify import musicbrainz


class _Response:
    def __init__(self, payload):
        self.payload = payload

    @staticmethod
    def raise_for_status():
        return None

    def json(self):
        return self.payload


def test_musicbrainz_enriches_high_confidence_match(monkeypatch):
    musicbrainz._CACHE.clear()

    def fake_get(*_args, **_kwargs):
        return _Response({
            'recordings': [
                {
                    'id': 'recording-1',
                    'title': 'The Correct Title',
                    'length': 180500,
                    'artist-credit': [{'name': 'The Artist'}],
                    'releases': [
                        {
                            'id': 'release-1',
                            'title': 'The Album',
                            'date': '2020-04-10',
                        }
                    ],
                }
            ]
        })

    monkeypatch.setattr(musicbrainz.requests, 'get', fake_get)

    result = musicbrainz.enrich_song_metadata({
        'name': 'The Correct Title',
        'artists': ['The Artist'],
        'album_name': 'The Album',
        'duration_ms': 180000,
    })

    assert result['name'] == 'The Correct Title'
    assert result['artists'] == ['The Artist']
    assert result['album_name'] == 'The Album'
    assert result['release_date'] == '2020-04-10'
    assert result['year'] == '2020'
    assert result['musicbrainz_recording_id'] == 'recording-1'
    assert result['musicbrainz_release_id'] == 'release-1'


def test_musicbrainz_rejects_weak_match(monkeypatch):
    musicbrainz._CACHE.clear()
    song = {
        'name': 'Original Song',
        'artists': ['Right Artist'],
        'album_name': 'Original Album',
    }

    def fake_get(*_args, **_kwargs):
        return _Response({
            'recordings': [
                {
                    'id': 'wrong-recording',
                    'title': 'Totally Different',
                    'artist-credit': [{'name': 'Wrong Artist'}],
                    'releases': [{'title': 'Wrong Album'}],
                }
            ]
        })

    monkeypatch.setattr(musicbrainz.requests, 'get', fake_get)

    assert musicbrainz.enrich_song_metadata(song) is song
