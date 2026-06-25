import { describe, expect, it } from 'vitest'

import {
  canOpenHistoryInPlayer,
  consumePlayerNavigation,
  resolvePlayerBrowseState,
  setPlayerNavigation,
} from '../model/playerNavigation'

describe('playerNavigation', () => {
  it('stores and consumes pending navigation once', () => {
    setPlayerNavigation({
      file: 'Artist/Album/Track.mp3',
      artist: 'Artist',
      album: 'Album',
    })
    expect(consumePlayerNavigation()).toEqual({
      file: 'Artist/Album/Track.mp3',
      artist: 'Artist',
      album: 'Album',
    })
    expect(consumePlayerNavigation()).toBeNull()
  })

  it('allows opening completed or skipped history rows with a filename', () => {
    expect(canOpenHistoryInPlayer({ status: 'done', filename: 'a.mp3' })).toBe(
      true
    )
    expect(
      canOpenHistoryInPlayer({ status: 'skipped', filename: 'a.mp3' })
    ).toBe(true)
    expect(canOpenHistoryInPlayer({ status: 'error', filename: 'a.mp3' })).toBe(
      false
    )
  })

  it('opens album tracks when the downloaded file belongs to an album', () => {
    const libraryItems = [
      {
        file: 'Artist/Album/One.mp3',
        title: 'One',
        artist: 'Artist',
        album: 'Album',
      },
      {
        file: 'Artist/Album/Two.mp3',
        title: 'Two',
        artist: 'Artist',
        album: 'Album',
      },
    ]

    const state = resolvePlayerBrowseState(libraryItems, {
      file: 'Artist/Album/Two.mp3',
      artist: 'Artist',
      album: 'Album',
    })

    expect(state.browseMode).toBe('albums')
    expect(state.selectedAlbumKey).toBe('Artist\u0000Album')
    expect(state.playlistFiles).toEqual([
      'Artist/Album/One.mp3',
      'Artist/Album/Two.mp3',
    ])
    expect(state.startFile).toBe('Artist/Album/Two.mp3')
  })

  it('falls back to artist tracks when album metadata is missing', () => {
    const libraryItems = [
      { file: 'Artist - Song A.mp3', title: 'Song A', artist: 'Artist' },
      { file: 'Artist - Song B.mp3', title: 'Song B', artist: 'Artist' },
    ]

    const state = resolvePlayerBrowseState(libraryItems, {
      file: 'Artist - Song B.mp3',
      artist: 'Artist',
    })

    expect(state.browseMode).toBe('artists')
    expect(state.selectedArtistName).toBe('Artist')
    expect(state.playlistFiles).toHaveLength(2)
  })
})
