import { describe, expect, it } from 'vitest'

import {
  filesWithFollowOnAlbum,
  nextAlbumAfter,
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
    expect(
      filesWithFollowOnAlbum(['a1.mp3', 'a2.mp3'], albums[1])
    ).toEqual({
      files: ['a1.mp3', 'a2.mp3', 'b1.mp3'],
      followOnStart: 2,
    })
  })
})
