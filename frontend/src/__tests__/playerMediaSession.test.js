import { describe, expect, it } from 'vitest'

import {
  artworkSourcesForTrack,
  mediaSessionPlaybackState,
} from '../model/playerMediaSession'

describe('playerMediaSession helpers', () => {
  it('maps player states to media session playback states', () => {
    expect(
      mediaSessionPlaybackState({ playing: true, paused: false, idle: false })
    ).toBe('playing')
    expect(
      mediaSessionPlaybackState({ playing: false, paused: true, idle: false })
    ).toBe('paused')
    expect(
      mediaSessionPlaybackState({ playing: false, paused: false, idle: true })
    ).toBe('none')
  })

  it('builds artwork metadata from http cover urls only', () => {
    expect(
      artworkSourcesForTrack({
        cover: 'https://example.com/cover.jpg',
      })
    ).toEqual([
      {
        src: 'https://example.com/cover.jpg',
        sizes: '512x512',
        type: 'image/jpeg',
      },
    ])
    expect(
      artworkSourcesForTrack({
        cover: 'blob:ignored',
      })
    ).toEqual([])
  })
})
