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
    isCapacitorNative: vi.fn(() => false),
    usesCustomServerUrl: vi.fn(() => false),
    needsServerConnection: vi.fn(() => false),
  }
})

describe('coverSourcesForNowPlaying', () => {
  beforeEach(async () => {
    const { isCapacitorNative } = await import('../model/serverConnection.js')
    isCapacitorNative.mockReturnValue(false)
    const API = (await import('../model/api.js')).default
    API.clearCoverSourcesCache()
  })

  it('uses 640px cover requests on web', async () => {
    const API = (await import('../model/api.js')).default

    const sources = API.coverSourcesForNowPlaying('Artist/Album/Track.m4a', {
      artistName: 'Artist',
    })

    expect(sources.src).toContain('size=640')
  })

  it('uses 320px cover requests on native embedded builds', async () => {
    const { isCapacitorNative } = await import('../model/serverConnection.js')
    isCapacitorNative.mockReturnValue(true)
    const API = (await import('../model/api.js')).default
    API.clearCoverSourcesCache()

    const sources = API.coverSourcesForNowPlaying('Artist/Album/Track.m4a', {
      artistName: 'Artist',
    })

    expect(sources.src).toContain('size=320')
    expect(sources.src).not.toContain('size=640')
  })
})
