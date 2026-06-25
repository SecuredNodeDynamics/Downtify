import { describe, expect, it } from 'vitest'

import { isSameAudioUrl, normalizeAudioUrl } from '../model/playerAudioUrl.js'

describe('player audio urls', () => {
  it('treats relative and absolute download paths as the same track', () => {
    const relative = '/downloads/Artist/Album/Track.mp3'
    const absolute = `http://localhost:8000${relative}`

    expect(normalizeAudioUrl(relative)).toBe(relative)
    expect(normalizeAudioUrl(absolute)).toBe(relative)
    expect(isSameAudioUrl(relative, absolute)).toBe(true)
  })

  it('detects different tracks', () => {
    expect(
      isSameAudioUrl(
        '/downloads/Artist/Album/One.mp3',
        '/downloads/Artist/Album/Two.mp3'
      )
    ).toBe(false)
  })
})
