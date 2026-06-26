import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../model/serverConnection.js', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    buildApiBaseUrl: () => 'http://127.0.0.1:8765',
    getServerConfig: () => ({
      PROTOCOL: 'http:',
      BACKEND: '127.0.0.1',
      PORT: '8765',
      BASEURL: '',
    }),
    isCapacitorNative: vi.fn(() => true),
    usesCustomServerUrl: vi.fn(() => false),
    needsServerConnection: vi.fn(() => false),
  }
})

const GOOGLE_COVER = 'https://lh3.googleusercontent.com/abc123=w600-h600-l90-rj'

describe('searchCoverUrl thumbnail downscaling', () => {
  beforeEach(async () => {
    const { isCapacitorNative } = await import('../model/serverConnection.js')
    isCapacitorNative.mockReturnValue(true)
  })

  it('downscales Google CDN covers to the tile size on native', async () => {
    const API = (await import('../model/api.js')).default
    expect(API.searchCoverUrl(GOOGLE_COVER)).toBe(
      'https://lh3.googleusercontent.com/abc123=w256-h256-l90-rj'
    )
  })

  it('honors an explicit display size for larger tiles', async () => {
    const API = (await import('../model/api.js')).default
    expect(API.searchCoverUrl(GOOGLE_COVER, 480)).toBe(
      'https://lh3.googleusercontent.com/abc123=w480-h480-l90-rj'
    )
  })

  it('appends a size suffix when the CDN url has none', async () => {
    const API = (await import('../model/api.js')).default
    expect(
      API.searchCoverUrl('https://lh3.googleusercontent.com/abc123', 256)
    ).toBe('https://lh3.googleusercontent.com/abc123=w256-h256-l90-rj')
  })

  it('leaves non-Google urls unchanged', async () => {
    const API = (await import('../model/api.js')).default
    const spotify = 'https://i.scdn.co/image/abc123'
    expect(API.searchCoverUrl(spotify)).toBe(spotify)
  })

  it('returns an empty string for empty input', async () => {
    const API = (await import('../model/api.js')).default
    expect(API.searchCoverUrl('')).toBe('')
  })
})
