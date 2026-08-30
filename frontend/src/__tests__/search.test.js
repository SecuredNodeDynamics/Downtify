import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../model/api.js', () => ({
  default: {
    search: vi.fn(),
  },
}))

const storage = new Map()

vi.stubGlobal('localStorage', {
  getItem: (key) => storage.get(key) ?? null,
  setItem: (key, value) => storage.set(key, value),
  removeItem: (key) => storage.delete(key),
  clear: () => storage.clear(),
})

import { useSearchManager } from '../model/search.js'

describe('search result filter', () => {
  beforeEach(() => {
    storage.clear()
  })

  it('filters albums and tracks from mixed results', () => {
    const sm = useSearchManager()
    const items = [
      { song_id: '1', media_type: 'track', name: 'Song' },
      { song_id: 'album:abc', media_type: 'album', name: 'Album' },
    ]

    sm.setResultFilter('both')
    expect(sm.filterResults(items)).toHaveLength(2)

    sm.setResultFilter('albums')
    expect(sm.filterResults(items)).toEqual([items[1]])

    sm.setResultFilter('tracks')
    expect(sm.filterResults(items)).toEqual([items[0]])

    sm.setResultFilter('artists')
    expect(sm.filterResults([
      ...items,
      { song_id: 'artist:1', media_type: 'artist', name: 'Band' },
    ])).toEqual([{ song_id: 'artist:1', media_type: 'artist', name: 'Band' }])
  })

  it('persists the selected filter', () => {
    const sm = useSearchManager()
    sm.setResultFilter('albums')
    expect(localStorage.getItem('downtify-search-result-filter')).toBe('albums')
    expect(sm.resultFilter.value).toBe('albums')
  })

  it('updates filteredResults when the filter changes', () => {
    const sm = useSearchManager()
    sm.setResultFilter('both')
    const items = [
      { song_id: '1', media_type: 'track', name: 'Song' },
      { song_id: 'album:abc', media_type: 'album', name: 'Album' },
    ]

    sm.results.value = items
    expect(sm.filteredResults.value).toHaveLength(2)

    sm.setResultFilter('albums')
    expect(sm.filteredResults.value).toEqual([items[1]])

    sm.setResultFilter('tracks')
    expect(sm.filteredResults.value).toEqual([items[0]])
  })
})

describe('search URL detection', () => {
  it('treats Spotify artist links as downloadable URLs', () => {
    const sm = useSearchManager()
    const url = 'https://open.spotify.com/artist/1nAVKAE4ylldkFvQGo58i8'
    expect(sm.isValidSearch(url)).toBe(false)
    expect(sm.isValidURL(url)).toBe(true)
    expect(sm.isValid(url)).toBe(true)
  })
})
