import { describe, expect, it, vi } from 'vitest'

import {
  artworkSourcesForTrack,
  createHeadsetClickRouter,
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
    expect(
      mediaSessionPlaybackState({ playing: false, paused: true, idle: true })
    ).toBe('paused')
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

  it('maps headset click counts to play, next, and previous', () => {
    vi.useFakeTimers()
    const toggle = vi.fn()
    const next = vi.fn()
    const previous = vi.fn()
    const router = createHeadsetClickRouter({
      toggle,
      next,
      previous,
      windowMs: 400,
    })

    router.onPlayPause()
    vi.advanceTimersByTime(400)
    expect(toggle).toHaveBeenCalledTimes(1)

    router.onPlayPause()
    router.onPlayPause()
    vi.advanceTimersByTime(400)
    expect(next).toHaveBeenCalledTimes(1)

    router.onPlayPause()
    router.onPlayPause()
    router.onPlayPause()
    vi.advanceTimersByTime(400)
    expect(previous).toHaveBeenCalledTimes(1)

    router.onPlayPause()
    router.cancel()
    vi.advanceTimersByTime(400)
    expect(toggle).toHaveBeenCalledTimes(1)
    vi.useRealTimers()
  })
})
