import { describe, expect, it } from 'vitest'

import {
  enrichTrackFromLibrary,
  filesWithFollowOnAlbum,
  nextAlbumAfter,
  nextGenrePlaylistStart,
  nextIndexInOrder,
  pickRandomStartIndex,
  prevIndexInOrder,
  resetGenrePlayStartMemory,
} from '../model/playerQueue.js'

describe('player up next album continuation', () => {
  const albums = [
    { name: 'Alpha', artist: 'Band', files: ['a1.mp3', 'a2.mp3'] },
    { name: 'Beta', artist: 'Band', files: ['b1.mp3'] },
    { name: 'Other', artist: 'Someone', files: ['o1.mp3'] },
  ]

  it('picks the next album by the same artist', () => {
    expect(nextAlbumAfter(albums, 'Band', 'Alpha')?.name).toBe('Beta')
    expect(nextAlbumAfter(albums, 'Band', 'Beta')).toBeNull()
  })

  it('appends follow-on album files after the current album', () => {
    expect(filesWithFollowOnAlbum(['a1.mp3', 'a2.mp3'], albums[1])).toEqual({
      files: ['a1.mp3', 'a2.mp3', 'b1.mp3'],
      followOnStart: 2,
    })
  })
})

describe('shuffle order wrapping', () => {
  const shuffleOrder = [2, 0, 1]

  it('stops at the end of a shuffle when repeat is off', () => {
    expect(
      nextIndexInOrder({
        length: 3,
        currentIndex: 1,
        shuffle: true,
        shuffleOrder,
        shufflePos: 2,
        repeatMode: 'off',
      })
    ).toBe(-1)
  })

  it('wraps shuffle only when repeating all', () => {
    expect(
      nextIndexInOrder({
        length: 3,
        currentIndex: 1,
        shuffle: true,
        shuffleOrder,
        shufflePos: 2,
        repeatMode: 'all',
      })
    ).toBe(2)
  })

  it('does not wrap shuffle prev when repeat is off', () => {
    expect(
      prevIndexInOrder({
        length: 3,
        currentIndex: 2,
        shuffle: true,
        shuffleOrder,
        shufflePos: 0,
        repeatMode: 'off',
      })
    ).toBe(-1)
  })
})

describe('library track display', () => {
  it('prefers library tags over filename parsing', () => {
    expect(
      enrichTrackFromLibrary(
        'Howard Shore/The Hobbit/01 The Clouds Burst.mp3',
        {
          title: 'The Clouds Burst',
          artist: 'Howard Shore',
          album: 'The Hobbit',
        }
      )
    ).toEqual({
      title: 'The Clouds Burst',
      artist: 'Howard Shore',
      album: 'The Hobbit',
    })
  })
})

describe('genre play start', () => {
  it('avoids indexes when picking a random start', () => {
    expect(pickRandomStartIndex(3, [0, 1], () => 0)).toBe(2)
    expect(pickRandomStartIndex(1, [0], () => 0)).toBe(0)
  })

  it('starts a different first track the next time a genre is played', () => {
    resetGenrePlayStartMemory()
    const files = ['a.mp3', 'b.mp3', 'c.mp3']
    expect(nextGenrePlaylistStart(files, [], () => 0)).toBe(0)
    expect(nextGenrePlaylistStart(files, [], () => 0)).toBe(1)
  })

  it('avoids the song that is already playing when starting a genre', () => {
    resetGenrePlayStartMemory()
    const files = ['a.mp3', 'b.mp3', 'c.mp3']
    expect(nextGenrePlaylistStart(files, ['a.mp3'], () => 0)).toBe(1)
  })
})
