import { describe, expect, it } from 'vitest'
import {
  albumFromPath,
  artistFromPath,
  groupAlbums,
  groupGenres,
  libraryCoverFolders,
  normalizeLibraryItem,
} from '../model/library.js'
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
})
