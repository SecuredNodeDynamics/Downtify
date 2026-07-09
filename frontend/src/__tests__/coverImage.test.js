import { describe, expect, it, vi } from 'vitest'
import {
  backendImageProxyUrl,
  buildCoverSourceKey,
  canLoadImageDirectly,
  getCachedCoverDisplay,
  invalidateFailedCoverDisplays,
  rememberCoverDisplay,
  resolveImageSrc,
} from '../model/imageLoader'

vi.mock('../model/serverConnection.js', () => ({
  buildApiBaseUrl: () => 'http://downtify.local:8000',
  getServerConfig: () => ({
    host: 'downtify.local',
    port: 8000,
    protocol: 'http',
  }),
  isCapacitorNative: vi.fn(() => false),
}))

vi.mock('../model/imageDiskCache.js', () => ({
  readPersistedImage: vi.fn(async () => null),
  writePersistedImage: vi.fn(async () => {}),
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

  it('drops failed cover cache entries so they can retry', () => {
    const sourceKey = buildCoverSourceKey('https://example.com/missing.jpg', [])
    rememberCoverDisplay(sourceKey, '', true)

    invalidateFailedCoverDisplays()

    expect(getCachedCoverDisplay(sourceKey)).toBeNull()
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

describe('resolveImageSrc direct URLs', () => {
  it('returns same-origin URLs immediately on native without preloading', async () => {
    const { isCapacitorNative } = await import('../model/serverConnection.js')
    const { readPersistedImage } = await import('../model/imageDiskCache.js')
    isCapacitorNative.mockReturnValue(true)
    readPersistedImage.mockResolvedValueOnce(null)

    const url = 'http://downtify.local:8000/cover?file=Artist%2Ftrack.mp3'
    await expect(resolveImageSrc(url)).resolves.toBe(url)
  })

  it('serves a persisted blob from disk on web so covers survive a reopen', async () => {
    const { isCapacitorNative } = await import('../model/serverConnection.js')
    const { readPersistedImage } = await import('../model/imageDiskCache.js')
    isCapacitorNative.mockReturnValue(false)

    const blob = new Blob(['fake-bytes'], { type: 'image/jpeg' })
    readPersistedImage.mockResolvedValueOnce(blob)

    const createObjectURL = vi
      .spyOn(URL, 'createObjectURL')
      .mockReturnValue('blob:persisted-cover')

    const url = 'https://web.test/cover?file=Artist%2Funique-web-track.mp3'
    await expect(resolveImageSrc(url)).resolves.toBe('blob:persisted-cover')
    expect(createObjectURL).toHaveBeenCalledWith(blob)

    createObjectURL.mockRestore()
  })

  it('builds a backend fallback for supported image CDNs only', () => {
    expect(backendImageProxyUrl('https://i.scdn.co/image/cover')).toContain(
      'http://downtify.local:8000/api/image-proxy?'
    )
    expect(backendImageProxyUrl('https://untrusted.test/cover.jpg')).toBe('')
  })
})
