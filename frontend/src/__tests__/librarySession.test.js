import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  clearLibrarySessionCache,
  getCachedLibraryItems,
  getCachedLibraryPaths,
  hydrateLibraryFromPersistence,
  loadPersistedLibrary,
  persistLibraryCache,
  resetLibraryPrefetch,
  setLibrarySessionCache,
  startLibraryPrefetch,
} from '../model/librarySession.js'

describe('librarySession', () => {
  beforeEach(() => {
    const store = new Map()
    vi.stubGlobal('localStorage', {
      getItem: (key) => store.get(key) ?? null,
      setItem: (key, value) => {
        store.set(key, value)
      },
      removeItem: (key) => {
        store.delete(key)
      },
      clear: () => {
        store.clear()
      },
    })
  })

  afterEach(() => {
    clearLibrarySessionCache()
    resetLibraryPrefetch()
    localStorage.clear()
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('hydrates the in-memory cache from persisted library data', () => {
    persistLibraryCache(
      ['Artist/Album/track.flac'],
      [
        {
          file: 'Artist/Album/track.flac',
          title: 'Track',
          artist: 'Artist',
          album: 'Album',
          genre: 'Rock',
          browse_genre: 'Rock',
        },
      ],
      'http://127.0.0.1:8000'
    )

    expect(hydrateLibraryFromPersistence('http://127.0.0.1:8000')).toBe(true)
    expect(getCachedLibraryPaths()).toEqual(['Artist/Album/track.flac'])
    expect(getCachedLibraryItems()?.[0]?.title).toBe('Track')
  })

  it('reuses an in-flight library prefetch promise', async () => {
    const fetchLibrary = vi.fn().mockResolvedValue([
      {
        file: 'Artist/track.flac',
        title: 'Track',
        artist: 'Artist',
        album: '',
        genre: '',
        browse_genre: '',
      },
    ])

    const first = startLibraryPrefetch(fetchLibrary, 'http://127.0.0.1:8000')
    const second = startLibraryPrefetch(fetchLibrary, 'http://127.0.0.1:8000')

    expect(first).toBe(second)
    await first

    expect(fetchLibrary).toHaveBeenCalledTimes(1)
    expect(getCachedLibraryItems()?.[0]?.file).toBe('Artist/track.flac')
    expect(loadPersistedLibrary('http://127.0.0.1:8000')?.items[0]?.file).toBe(
      'Artist/track.flac'
    )
  })

  it('stores session cache entries for player hydration', () => {
    setLibrarySessionCache(
      ['Artist/track.flac'],
      [
        {
          file: 'Artist/track.flac',
          title: 'Track',
          artist: 'Artist',
          album: '',
          genre: '',
          browse_genre: '',
        },
      ]
    )

    expect(getCachedLibraryPaths()).toEqual(['Artist/track.flac'])
    expect(getCachedLibraryItems()).toHaveLength(1)
  })
})
