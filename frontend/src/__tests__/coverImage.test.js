import { describe, expect, it, vi } from 'vitest'

import {
  buildCoverSourceKey,
  canLoadImageDirectly,
  getCachedCoverDisplay,
  rememberCoverDisplay,
} from '../model/imageLoader'

vi.mock('../model/serverConnection.js', () => ({
  buildApiBaseUrl: () => 'http://downtify.local:8000',
  getServerConfig: () => ({ host: 'downtify.local', port: 8000, protocol: 'http' }),
  isCapacitorNative: vi.fn(() => false),
}))

describe('imageLoader cover cache', () => {
  it('builds stable source keys for cover candidates', () => {
    expect(
      buildCoverSourceKey('https://a.test/1.jpg', ['https://a.test/2.jpg'])
    ).toBe('https://a.test/1.jpg\0https://a.test/2.jpg')
  })

  it('stores and restores resolved cover display values', () => {
    const sourceKey = buildCoverSourceKey('https://example.com/cover.jpg', [])
    rememberCoverDisplay(sourceKey, 'blob:cached-cover', false)

    expect(getCachedCoverDisplay(sourceKey)).toEqual({
      displaySrc: 'blob:cached-cover',
      failed: false,
    })
  })
})

describe('canLoadImageDirectly', () => {
  it('allows same-origin server URLs on native', async () => {
    const { isCapacitorNative } = await import('../model/serverConnection.js')
    isCapacitorNative.mockReturnValue(true)

    expect(
      canLoadImageDirectly(
        'http://downtify.local:8000/cover?artist=Test&file=track.mp3'
      )
    ).toBe(true)
    expect(canLoadImageDirectly('https://i.scdn.co/image/abc')).toBe(false)
  })

  it('allows any HTTP URL on web', async () => {
    const { isCapacitorNative } = await import('../model/serverConnection.js')
    isCapacitorNative.mockReturnValue(false)

    expect(canLoadImageDirectly('https://i.scdn.co/image/abc')).toBe(true)
  })
})
