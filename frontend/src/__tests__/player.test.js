import { describe, expect, it } from 'vitest'

import {
  isSameAudioFile,
  isSameAudioUrl,
  normalizeAudioUrl,
} from '../model/playerAudioUrl.js'

describe('player audio urls', () => {
  it('treats relative and absolute download paths as the same track', () => {
    const relative = '/downloads/Artist/Album/Track.mp3'
    const absolute = `http://localhost:8000${relative}`

    expect(normalizeAudioUrl(relative)).toBe(relative)
    expect(normalizeAudioUrl(absolute)).toBe(relative)
    expect(isSameAudioUrl(relative, absolute)).toBe(true)
  })

  it('normalizes capacitor file bridge urls to filesystem paths', () => {
    const capacitor =
      'http://localhost/_capacitor_file_/storage/emulated/0/Music/Downtify/Artist%20-%20Song.m4a'
    expect(normalizeAudioUrl(capacitor)).toBe(
      '/storage/emulated/0/Music/Downtify/Artist - Song.m4a'
    )
  })

  it('matches capacitor playback urls to library file paths', () => {
    const capacitor =
      'http://localhost/_capacitor_file_/storage/emulated/0/Music/Downtify/Artist%20-%20Song.m4a'
    expect(isSameAudioFile(capacitor, 'Artist - Song.m4a')).toBe(true)
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
