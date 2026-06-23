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
  })

  it('persists the selected filter', () => {
    const sm = useSearchManager()
    sm.setResultFilter('albums')
    expect(localStorage.getItem('downtify-search-result-filter')).toBe('albums')
    expect(sm.resultFilter.value).toBe('albums')
  })
})
