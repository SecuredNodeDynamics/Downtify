import { describe, expect, it } from 'vitest'

import {
  buildSearchRoute,
  resolveSearchRouteQuery,
} from '../model/searchNavigation.js'

describe('search navigation', () => {
  it('builds query-string routes for text and spotify URLs', () => {
    expect(buildSearchRoute('Perfect Ed Sheeran')).toEqual({
      name: 'Search',
      query: { q: 'Perfect Ed Sheeran' },
    })
    expect(
      buildSearchRoute('https://open.spotify.com/track/6vIpkg9mdc5kDYvwuO6Qtc')
    ).toEqual({
      name: 'Search',
      query: {
        q: 'https://open.spotify.com/track/6vIpkg9mdc5kDYvwuO6Qtc',
      },
    })
  })

  it('reads modern and legacy search routes', () => {
    expect(
      resolveSearchRouteQuery({
        query: { q: 'https://open.spotify.com/track/abc' },
        params: {},
      })
    ).toBe('https://open.spotify.com/track/abc')

    expect(
      resolveSearchRouteQuery({
        query: {},
        params: { query: 'Perfect%20Ed%20Sheeran' },
      })
    ).toBe('Perfect Ed Sheeran')
  })
})
