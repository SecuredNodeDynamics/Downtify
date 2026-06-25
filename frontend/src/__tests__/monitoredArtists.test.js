import { describe, expect, it } from 'vitest'

import {
  findMonitoredArtist,
  monitoredArtistMap,
  monitoredArtists,
  normalizeMonitoredArtistName,
} from '../model/monitoredArtists.js'

describe('monitoredArtists', () => {
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
})
