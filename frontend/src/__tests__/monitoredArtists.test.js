import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  findMonitoredArtist,
  monitoredArtistMap,
  monitoredArtists,
  normalizeMonitoredArtistName,
  upsertMonitoredArtist,
} from '../model/monitoredArtists.js'

describe('monitoredArtists', () => {
  beforeEach(() => {
    const store = new Map()
    vi.stubGlobal('sessionStorage', {
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
    monitoredArtists.value = []
    monitoredArtistMap.value = new Map()
    sessionStorage.clear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('matches artist monitors case-insensitively', () => {
    monitoredArtists.value = [
      { id: 1, kind: 'artist', name: 'Taylor Swift', enabled: true },
      { id: 2, kind: 'playlist', name: 'Daily Mix', enabled: true },
    ]
    monitoredArtistMap.value = new Map([
      ['taylor swift', monitoredArtists.value[0]],
    ])

    expect(normalizeMonitoredArtistName('  Taylor Swift ')).toBe('taylor swift')
    expect(findMonitoredArtist('taylor swift')).toEqual(monitoredArtists.value[0])
    expect(findMonitoredArtist('Daily Mix')).toBeNull()
  })

  it('links a library artist name to a monitored Spotify artist', () => {
    upsertMonitoredArtist(
      { id: 3, kind: 'artist', name: 'The Weeknd', enabled: true },
      'Weeknd'
    )

    expect(findMonitoredArtist('Weeknd')).toEqual(monitoredArtists.value[0])
    expect(findMonitoredArtist('The Weeknd')).toEqual(monitoredArtists.value[0])
  })

  it('dedupes monitored artists by spotify id and name', () => {
    upsertMonitoredArtist({
      id: 1,
      kind: 'artist',
      spotify_id: 'abc',
      name: 'Taylor Swift',
      enabled: true,
    })
    upsertMonitoredArtist({
      id: 2,
      kind: 'artist',
      spotify_id: 'abc',
      name: 'Taylor Swift',
      enabled: true,
    })

    expect(monitoredArtists.value).toHaveLength(1)
    expect(monitoredArtists.value[0].id).toBe(2)
  })
})
