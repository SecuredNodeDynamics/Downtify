from downtify import genres
from downtify.genres import browse_genre, canonical_genre, pick_genre_from_tags


def test_canonical_genre_rejects_non_genre_tags():
    assert canonical_genre('Composer') == ''
    assert canonical_genre('Guitar Player') == ''
    assert canonical_genre('French') == ''
    assert canonical_genre('Academy Award Winner') == ''


def test_canonical_genre_accepts_spotify_style_tags():
    assert canonical_genre('indie pop') == 'Indie Pop'
    assert canonical_genre('neo soul') == 'Neo Soul'
    assert canonical_genre('smooth jazz') == 'Smooth Jazz'
    assert canonical_genre('classical crossover') == 'Classical Crossover'


def test_browse_genre_maps_to_spotify_categories():
    assert browse_genre('Indie Pop') == 'Indie'
    assert browse_genre('Neo Soul') == 'R&B'
    assert browse_genre('Smooth Jazz') == 'Jazz'
    assert browse_genre('Country Rap') == 'Country'
    assert browse_genre('Modern Classical') == 'Classical'


def test_pick_genre_from_tags_skips_junk_musicbrainz_tags():
    tags = [
        {'name': 'composer', 'count': 100},
        {'name': 'classical', 'count': 40},
    ]
    assert pick_genre_from_tags(tags) == 'Classical'


def test_pick_genre_from_tags_prefers_higher_ranked_valid_tag():
    tags = [
        {'name': 'british', 'count': 90},
        {'name': 'indie rock', 'count': 20},
    ]
    assert pick_genre_from_tags(tags) == 'Indie Rock'
