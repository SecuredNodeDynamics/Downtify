import { describe, expect, it } from 'vitest'

import {
  isFieldHiddenByKeyboard,
  isMobileViewport,
  shouldTrackFieldVisibility,
} from '../model/searchFieldVisibility'

describe('searchFieldVisibility', () => {
  it('treats phone-width viewports as mobile', () => {
    expect(isMobileViewport(390)).toBe(true)
    expect(isMobileViewport(1023)).toBe(true)
    expect(isMobileViewport(1024)).toBe(false)
    expect(isMobileViewport(0)).toBe(false)
    expect(isMobileViewport(undefined)).toBe(false)
  })

  it('only tracks visibility when enabled on a mobile viewport', () => {
    expect(
      shouldTrackFieldVisibility({ enabled: true, viewportWidth: 390 })
    ).toBe(true)
    expect(
      shouldTrackFieldVisibility({ enabled: false, viewportWidth: 390 })
    ).toBe(false)
    expect(
      shouldTrackFieldVisibility({ enabled: true, viewportWidth: 1440 })
    ).toBe(false)
    expect(shouldTrackFieldVisibility()).toBe(false)
  })

  it('detects a field hidden behind the keyboard', () => {
    // Visible area is 0..400 (keyboard shrank the viewport). Field bottom at 560
    // sits well below it, so it is hidden.
    expect(
      isFieldHiddenByKeyboard({
        fieldTop: 500,
        fieldBottom: 560,
        viewportOffsetTop: 0,
        viewportHeight: 400,
        margin: 16,
      })
    ).toBe(true)
  })

  it('treats a comfortably visible field as not hidden', () => {
    expect(
      isFieldHiddenByKeyboard({
        fieldTop: 120,
        fieldBottom: 180,
        viewportOffsetTop: 0,
        viewportHeight: 400,
        margin: 16,
      })
    ).toBe(false)
  })

  it('detects a field scrolled above the visible viewport', () => {
    expect(
      isFieldHiddenByKeyboard({
        fieldTop: 10,
        fieldBottom: 70,
        viewportOffsetTop: 100,
        viewportHeight: 400,
        margin: 16,
      })
    ).toBe(true)
  })

  it('does nothing without a usable viewport height', () => {
    expect(
      isFieldHiddenByKeyboard({
        fieldTop: 500,
        fieldBottom: 560,
        viewportHeight: 0,
      })
    ).toBe(false)
    expect(isFieldHiddenByKeyboard()).toBe(false)
  })
})
