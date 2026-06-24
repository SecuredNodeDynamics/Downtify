import { describe, expect, it } from 'vitest'

import {
  buildCoverSourceKey,
  getCachedCoverDisplay,
  rememberCoverDisplay,
} from '../model/imageLoader'

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
})
