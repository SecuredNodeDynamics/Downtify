import { describe, expect, it } from 'vitest'

import {
  countOverflowSettingsTabs,
  settingsTabsNeedMenu,
} from '../model/settingsTabsOverflow.js'

describe('settingsTabsNeedMenu', () => {
  it('keeps the full tab row when every label fits', () => {
    expect(
      settingsTabsNeedMenu({
        tabWidths: [72, 80, 48, 56, 64, 52],
        gap: 4,
        available: 640,
      })
    ).toBe(false)
    expect(
      countOverflowSettingsTabs({
        tabWidths: [72, 80, 48, 56, 64, 52],
        gap: 4,
        available: 640,
      })
    ).toBe(0)
  })

  it('opens the menu when the labels would wrap', () => {
    expect(
      settingsTabsNeedMenu({
        tabWidths: [90, 90, 90, 90, 90, 90],
        gap: 4,
        available: 360,
      })
    ).toBe(true)
    expect(
      countOverflowSettingsTabs({
        tabWidths: [90, 90, 90, 90, 90, 90],
        gap: 4,
        available: 360,
      })
    ).toBe(1)
  })
})
