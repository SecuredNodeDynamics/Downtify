"""Spotify-style genre normalization and browse grouping."""

from __future__ import annotations

import re
from typing import Any

_BROWSE_GENRES: tuple[str, ...] = (
    'Pop',
    'Rock',
    'Hip-Hop',
    'R&B',
    'Electronic',
    'Dance',
    'Latin',
    'Jazz',
    'Classical',
    'Country',
    'Metal',
    'Indie',
    'Folk',
    'Reggae',
    'Blues',
    'Soul',
    'Funk',
    'Punk',
    'Soundtrack',
    'World',
)

_NON_GENRE_EXACT: frozenset[str] = frozenset({
    'academy award winner',
    'american',
    'british',
    'british choir',
    'choir',
    'composer',
    'conductor',
    'female vocalists',
    'film composer',
    'finnish',
    'french',
    'german',
    'guitar player',
    'guitarist',
    'instrumental',
    'male vocalists',
    'musician',
    'orchestra',
    'pianist',
    'producer',
    'seen live',
    'singer',
    'songwriter',
    'soprano',
    'tenor',
    'under 2000 listeners',
    'vocalist',
    'vocalists',
})

_GENRE_SUFFIXES: tuple[str, ...] = (
    'rock',
    'pop',
    'jazz',
    'metal',
    'hop',
    'wave',
    'core',
    'house',
    'step',
    'folk',
    'blues',
    'soul',
    'funk',
    'punk',
    'disco',
    'techno',
    'trance',
    'ambient',
    'classical',
    'country',
    'reggae',
    'latin',
    'gospel',
    'grunge',
    'ska',
)

_BROWSE_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
    (('hip hop', 'hip-hop', 'rap', 'trap', 'drill', 'grime', 'gangsta'), 'Hip-Hop'),
    (('r&b', 'rnb', 'neo soul', 'contemporary r&b'), 'R&B'),
    (('soul', 'motown'), 'Soul'),
    (('funk', 'boogie'), 'Funk'),
    (
        (
            'electronic',
            'edm',
            'house',
            'techno',
            'trance',
            'dubstep',
            'ambient',
            'synth',
            'electro',
            'downtempo',
            'idm',
        ),
        'Electronic',
    ),
    (('dance', 'disco', 'eurodance'), 'Dance'),
    (
        ('latin', 'reggaeton', 'salsa', 'bachata', 'cumbia', 'merengue', 'latin pop'),
        'Latin',
    ),
    (('jazz', 'bebop', 'swing', 'smooth jazz'), 'Jazz'),
    (
        (
            'classical',
            'orchestral',
            'symphony',
            'baroque',
            'opera',
            'chamber',
            'romantic',
            'modern classical',
            'classical crossover',
            'cinematic classical',
        ),
        'Classical',
    ),
    (('country', 'bluegrass', 'americana', 'country rap'), 'Country'),
    (
        ('metal', 'hardcore', 'death metal', 'thrash', 'black metal', 'heavy metal'),
        'Metal',
    ),
    (('punk', 'post-punk', 'emo'), 'Punk'),
    (('indie', 'indie rock', 'indie pop', 'shoegaze'), 'Indie'),
    (('folk', 'acoustic', 'singer-songwriter'), 'Folk'),
    (('reggae', 'dub', 'ska', 'dancehall'), 'Reggae'),
    (('blues', 'delta blues'), 'Blues'),
    (
        ('rock', 'alternative', 'grunge', 'post-rock', 'hard rock', 'classic rock'),
        'Rock',
    ),
    (('pop', 'k-pop', 'j-pop', 'synth-pop', 'dance pop', 'art pop'), 'Pop'),
    (
        ('soundtrack', 'score', 'film score', 'film', 'game soundtrack', 'ost'),
        'Soundtrack',
    ),
    (('world', 'afrobeat', 'celtic', 'flamenco', 'bossa nova'), 'World'),
    (('gospel', 'christian', 'worship'), 'World'),
    (('ballad',), 'Pop'),
)

_SLUG_RE = re.compile(r'[^a-z0-9&]+')


def _slug(value: str) -> str:
    text = str(value or '').strip().casefold()
    text = text.replace('&', ' and ')
    text = _SLUG_RE.sub(' ', text)
    return ' '.join(text.split())


def _title_case_genre(value: str) -> str:
    raw = ' '.join(str(value or '').strip().split())
    if not raw:
        return ''
    folded = raw.casefold().replace('-', ' ')
    if folded in {'r&b', 'rnb', 'r and b'}:
        return 'R&B'
    if folded in {'hip hop', 'hiphop'}:
        return 'Hip-Hop'
    if raw.casefold() in {'edm', 'idm'}:
        return raw.upper()
    return raw.title()


def _split_genre_parts(value: str) -> list[str]:
    raw = str(value or '').strip()
    if not raw:
        return []
    for separator in (';', '/', '|'):
        if separator in raw:
            return [part.strip() for part in raw.split(separator) if part.strip()]
    if ',' in raw:
        return [part.strip() for part in raw.split(',') if part.strip()]
    return [raw]


def is_non_genre_tag(value: str) -> bool:
    slug = _slug(value)
    if not slug:
        return True
    if slug in _NON_GENRE_EXACT:
        return True
    if slug in {'american', 'british', 'french', 'finnish', 'german', 'spanish'}:
        return True
    if slug.endswith(' composer'):
        return True
    if slug.endswith(' choir'):
        return True
    return False


def is_recognized_genre(value: str) -> bool:
    slug = _slug(value)
    if not slug or is_non_genre_tag(slug):
        return False
    for keywords, _parent in _BROWSE_RULES:
        for keyword in keywords:
            if slug == keyword or keyword in slug:
                return True
    for suffix in _GENRE_SUFFIXES:
        if slug == suffix or slug.endswith(f' {suffix}'):
            return True
    return False


def normalize_genre_label(value: str) -> str:
    for part in _split_genre_parts(value):
        if is_recognized_genre(part):
            return _title_case_genre(part)
    return ''


def canonical_genre(value: str) -> str:
    """Return a cleaned Spotify-style genre label or an empty string."""

    return normalize_genre_label(value)


def browse_genre(value: str) -> str:
    """Map a genre label to a Spotify-style browse category."""

    slug = _slug(value)
    if not slug:
        return ''
    matches: list[tuple[int, str]] = []
    for keywords, parent in _BROWSE_RULES:
        for keyword in keywords:
            if slug == keyword or keyword in slug:
                matches.append((len(keyword), parent))
    if matches:
        return max(matches, key=lambda item: item[0])[1]
    if is_recognized_genre(slug):
        return _title_case_genre(value)
    return ''


def pick_genre_from_tags(tags: Any) -> str:
    """Pick the best genre from a MusicBrainz-style tag list."""

    if not isinstance(tags, list):
        return ''
    ranked = [
        item
        for item in tags
        if isinstance(item, dict) and str(item.get('name') or '').strip()
    ]
    if not ranked:
        return ''
    ranked.sort(key=lambda item: int(item.get('count') or 0), reverse=True)
    for item in ranked:
        genre = canonical_genre(str(item.get('name') or ''))
        if genre:
            return genre
    return ''


def pick_genre_from_tag_names(names: list[str]) -> str:
    """Pick the best genre from plain tag names (e.g. Last.fm)."""

    for name in names:
        genre = canonical_genre(name)
        if genre:
            return genre
    return ''


def browse_genres() -> tuple[str, ...]:
    return _BROWSE_GENRES
