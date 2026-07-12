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

  it('uses folder previews before embedded track covers for genre tiles', async () => {
    const API = (await import('../model/api.js')).default

    const sources = API.coverSourcesForGenreFile('Artist/Album/Track.m4a')

    expect(sources.src).toContain('/api/metadata/artist-images/folder-preview?')
    expect(sources.src).toContain('folder=Artist%2FAlbum')
    expect(sources.fallbacks.at(-1)).toContain('/cover?')
  })

  it('uses folder previews before embedded track covers for album tiles', async () => {
    const API = (await import('../model/api.js')).default

    const sources = API.coverSourcesForAlbumFile('Artist/Album/Track.m4a')

    expect(sources.src).toContain('/api/metadata/artist-images/folder-preview?')
    expect(sources.src).toContain('folder=Artist%2FAlbum')
    expect(sources.fallbacks.at(-1)).toContain('/cover?')
  })

  it('provides proxy and direct fallbacks for remote artwork', async () => {
    const API = (await import('../model/api.js')).default
    const remote = 'https://yt3.googleusercontent.com/example=w600-h600-l90-rj'

    const sources = API.remoteCoverSources(remote, 192)

    expect(sources.src).toContain('/api/image-proxy?')
    expect(sources.src).toContain('w192-h192')
    expect(sources.fallbacks).toEqual([
      'https://yt3.googleusercontent.com/example=w192-h192-l90-rj',
    ])
  })
})
