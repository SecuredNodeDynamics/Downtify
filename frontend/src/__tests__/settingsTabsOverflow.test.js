import { describe, expect, it } from 'vitest'

import { countOverflowSettingsTabs } from '../model/settingsTabsOverflow.js'

describe('countOverflowSettingsTabs', () => {
  it('keeps every tab when they fit on one row', () => {
    expect(
      countOverflowSettingsTabs({
        tabWidths: [72, 80, 48, 56, 64, 52],
        moreWidth: 44,
        gap: 4,
        available: 640,
      })
    ).toBe(0)
  })

  it('moves trailing tabs into the menu when the row would wrap', () => {
    expect(
      countOverflowSettingsTabs({
        tabWidths: [90, 90, 90, 90, 90, 90],
        moreWidth: 44,
        gap: 4,
        available: 360,
      })
    ).toBe(3)
  })

  it('always leaves at least one tab visible', () => {
    expect(
      countOverflowSettingsTabs({
        tabWidths: [200, 200, 200],
        moreWidth: 40,
        gap: 4,
        available: 80,
      })
    ).toBe(2)
  })
})
