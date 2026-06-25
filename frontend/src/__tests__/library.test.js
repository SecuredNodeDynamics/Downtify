import { describe, expect, it } from 'vitest'
import {
  albumFromPath,
  artistFromPath,
  groupAlbums,
  groupArtists,
  groupGenres,
  libraryGenreName,
  libraryItemsEqual,
  libraryCoverFolders,
  matchesLibraryAlbumEntry,
  matchesLibraryArtistName,
  matchesLibraryField,
  matchesLibraryFilter,
  matchesLibraryGenreName,
  matchesLibraryTrackItem,
  normalizeLibraryItem,
} from '../model/library.js'
import {
  filterOnlineResultsForLibraryView,
  onlineArtistsLabel,
} from '../model/libraryOnlineSearch.js'
import { genreCoverIcon, genreCoverStyle } from '../model/genreArt.js'

describe('library path helpers', () => {
  it('derives artist and album from nested paths', () => {
    const file = 'Aaron Copland/Hollywood/01 - Fanfare.mp3'
    expect(artistFromPath(file)).toBe('Aaron Copland')
    expect(albumFromPath(file)).toBe('Hollywood')
  })

  it('groups albums from path-only library items', () => {
    const items = [
      { file: 'Aaron Copland/Hollywood/01 - Fanfare.mp3', title: 'Fanfare' },
      { file: 'Aaron Copland/Hollywood/02 - Rodeo.mp3', title: 'Rodeo' },
    ]

    const albums = groupAlbums(items)
    expect(albums).toHaveLength(1)
    expect(albums[0].name).toBe('Hollywood')
    expect(albums[0].artist).toBe('Aaron Copland')
    expect(albums[0].files).toHaveLength(2)
  })

  it('virtually groups collaborations under each credited artist', () => {
    const items = [
      {
        file: 'Connor Price/Swing/01.flac',
        artist: 'Connor Price',
        artists: ['Connor Price', 'Nic D', '4Korners'],
        album: 'Swing',
        title: 'Swing',
      },
    ]

    const artists = groupArtists(items)
    expect(artists.map((artist) => artist.name).sort()).toEqual([
      '4Korners',
      'Connor Price',
      'Nic D',
    ])

    const albums = groupAlbums(items)
    expect(albums).toHaveLength(3)
    expect(
      albums.find((album) => album.artist === 'Nic D')?.files
    ).toEqual(['Connor Price/Swing/01.flac'])
    expect(matchesLibraryTrackItem(items[0], 'Nic D')).toBe(true)
    expect(
      matchesLibraryAlbumEntry(
        {
          name: 'Swing',
          artist: 'Nic D',
          artists: ['Connor Price', 'Nic D', '4Korners'],
        },
        '4Korners'
      )
    ).toBe(true)
  })

  it('normalizes sparse items and buckets unknown genres', () => {
    const item = normalizeLibraryItem({
      file: 'Artist/Album/track.flac',
      title: '',
      artist: '',
      album: '',
      genre: '',
    })

    expect(item.artist).toBe('Artist')
    expect(item.album).toBe('Album')

    const genres = groupGenres([item], 'Unknown genre')
    expect(genres).toHaveLength(1)
    expect(genres[0].name).toBe('Unknown genre')
  })

  it('merges hip hop genre spelling variants into one bucket', () => {
    const items = [
      {
        file: 'Artist A/Album/01.flac',
        genre: 'Hip Hop',
        browse_genre: 'Hip-Hop',
      },
      {
        file: 'Artist B/Album/01.flac',
        genre: 'Hip-Hop',
        browse_genre: 'Hip-Hop',
      },
    ]

    const genres = groupGenres(items)
    expect(genres).toHaveLength(1)
    expect(genres[0].name).toBe('Hip-Hop')
    expect(genres[0].files).toHaveLength(2)
  })

  it('groups specific genres like Swing instead of collapsing to browse parents', () => {
    const items = [
      {
        file: 'Swing Sisters/Swing/01.flac',
        genre: 'Swing',
        browse_genre: 'Jazz',
      },
      {
        file: 'Swing Sisters/Swing/02.flac',
        genre: 'Swing',
        browse_genre: 'Jazz',
      },
    ]

    const genres = groupGenres(items)
    expect(genres).toHaveLength(1)
    expect(genres[0].name).toBe('Swing')
    expect(genres[0].subgenres).toEqual(['Jazz'])
    expect(libraryGenreName(items[0])).toBe('Swing')
  })

  it('groups genre cover files from distinct albums', () => {
    const items = [
      { file: 'Artist/Album A/01.flac', browse_genre: 'Pop' },
      { file: 'Artist/Album A/02.flac', browse_genre: 'Pop' },
      { file: 'Artist/Album B/01.flac', browse_genre: 'Pop' },
      { file: 'Other/Album C/01.flac', browse_genre: 'Pop' },
    ]

    const genres = groupGenres(items)
    expect(genres).toHaveLength(1)
    expect(genres[0].coverFiles).toEqual([
      'Artist/Album A/01.flac',
      'Artist/Album B/01.flac',
      'Other/Album C/01.flac',
    ])
  })

  it('provides genre art fallbacks for browse categories', () => {
    expect(genreCoverStyle('Jazz').background).toContain('gradient')
    expect(genreCoverIcon('Jazz')).toBeTruthy()
    expect(genreCoverIcon('Unknown Genre')).toBeTruthy()
  })

  it('lists album and artist folders for cover fallbacks', () => {
    expect(libraryCoverFolders('Aaron Copland/Hollywood/track.mp3')).toEqual([
      'Aaron Copland/Hollywood',
      'Aaron Copland',
    ])
    expect(libraryCoverFolders('Aaron Copland/track.mp3')).toEqual([
      'Aaron Copland',
    ])
  })

  it('matches library search only on primary artist, album, and track fields', () => {
    const kennyTrack = normalizeLibraryItem({
      file: 'Michael Bolton/The Essential Kenny G/01 - Song.mp3',
      title: 'Song',
      artist: 'Michael Bolton',
      album: 'The Essential Kenny G',
      genre: 'Kenny G',
    })
    const kennyArtist = normalizeLibraryItem({
      file: 'Kenny G/Breathless/01 - Track.mp3',
      title: 'Track',
      artist: 'Kenny G',
      album: 'Breathless',
    })

    expect(matchesLibraryArtistName('Kenny G', 'Kenny G')).toBe(true)
    expect(matchesLibraryArtistName('Michael Bolton', 'Kenny G')).toBe(false)
    expect(matchesLibraryArtistName('Matué', 'Kenny G')).toBe(false)

    expect(
      matchesLibraryAlbumEntry(
        { name: 'The Essential Kenny G', artist: 'Michael Bolton' },
        'Kenny G'
      )
    ).toBe(true)
    expect(
      matchesLibraryAlbumEntry(
        { name: 'Breathless', artist: 'Kenny G' },
        'Kenny G'
      )
    ).toBe(true)
    expect(
      matchesLibraryAlbumEntry(
        { name: 'Random', artist: 'Rip Kane' },
        'Kenny G'
      )
    ).toBe(false)

    expect(matchesLibraryTrackItem(kennyArtist, 'Kenny G')).toBe(true)
    expect(matchesLibraryTrackItem(kennyTrack, 'Kenny G')).toBe(true)
    expect(
      matchesLibraryFilter(
        normalizeLibraryItem({
          file: 'Rip Kane/Album/track.mp3',
          title: 'Unrelated',
          artist: 'Rip Kane',
          album: 'Album',
          genre: 'Kenny G',
        }),
        'Kenny G'
      )
    ).toBe(false)
  })

  it('filters online download offers by library tab', () => {
    const items = [
      {
        media_type: 'album',
        name: 'Breathless',
        artists: ['Kenny G'],
        browse_id: 'album:1',
      },
      {
        media_type: 'track',
        name: 'Song',
        artists: ['Michael Bolton'],
        album_name: 'The Essential Kenny G',
        song_id: 'track:1',
      },
      {
        media_type: 'track',
        name: 'Honey',
        artists: ['Kenny G'],
        album_name: 'Breathless',
        song_id: 'track:2',
      },
    ]

    const artistMatches = filterOnlineResultsForLibraryView(
      items,
      'artists',
      'Kenny G'
    )
    expect(artistMatches.map((item) => onlineArtistsLabel(item))).toEqual([
      'Kenny G',
      'Kenny G',
    ])

    expect(
      filterOnlineResultsForLibraryView(items, 'albums', 'Kenny G')
    ).toHaveLength(1)
    expect(
      filterOnlineResultsForLibraryView(items, 'tracks', 'Kenny G')
    ).toHaveLength(2)
  })

  it('detects unchanged library items including artists metadata', () => {
    const items = [
      {
        file: 'Artist/Album/track.mp3',
        title: 'Track',
        artist: 'Artist',
        artists: ['Artist', 'Guest'],
        album: 'Album',
        genre: 'Pop',
        browse_genre: 'Pop',
      },
    ]
    const normalized = [
      {
        file: 'Artist/Album/track.mp3',
        title: 'Track',
        artist: 'Artist',
        artists: ['Artist', 'Guest'],
        album: 'Album',
        genre: 'Pop',
        browse_genre: 'Pop',
      },
    ]
    expect(libraryItemsEqual(items, normalized)).toBe(true)
    expect(
      libraryItemsEqual(items, [
        { ...normalized[0], artists: ['Artist', 'Other'] },
      ])
    ).toBe(false)
  })
})
