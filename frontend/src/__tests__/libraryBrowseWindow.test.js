import { describe, expect, it } from 'vitest'

import {
  libraryGridColumns,
  libraryGridRowSize,
  virtualBrowseWindow,
} from '../model/libraryBrowseWindow.js'

describe('libraryBrowseWindow', () => {
  it('picks grid columns by width', () => {
    expect(libraryGridColumns(375)).toBe(2)
    expect(libraryGridColumns(640)).toBe(3)
    expect(libraryGridColumns(1200)).toBe(4)
  })

  it('estimates grid row height from tile width plus body and gap', () => {
    expect(
      libraryGridRowSize({
        containerWidth: 351,
        columns: 2,
        bodyHeight: 72,
        gap: 12,
      })
    ).toBe(254)
  })

  it('windows a long track list around the viewport', () => {
    const window = virtualBrowseWindow({
      count: 400,
      columns: 1,
      itemSize: 80,
      scrollTop: 1600,
      viewportHeight: 640,
      overscanRows: 2,
    })
    expect(window.start).toBe(18)
    expect(window.end).toBe(30)
    expect(window.padTop).toBe(1440)
    expect(window.padBottom).toBeGreaterThan(0)
  })
})
