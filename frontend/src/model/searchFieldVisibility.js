// Mobile viewports (phones / the Capacitor APK WebView) show an on-screen
// keyboard that can cover a focused search field. These helpers decide whether
// a field needs to be scrolled back into the visible area above the keyboard.

// The largest viewport width still treated as "mobile" (matches the CSS
// breakpoint where the fixed-height, single-scroll-container layout applies).
export const MOBILE_MAX_WIDTH = 1023

// Re-center attempts after focus, in milliseconds. The keyboard animates in and
// (on Android) resizes the viewport asynchronously, so a couple of delayed
// passes catch platforms that don't emit a visualViewport resize event.
export const FIELD_VISIBILITY_RETRY_DELAYS_MS = [150, 450]

export function isMobileViewport(width) {
  const value = Number(width)
  if (!Number.isFinite(value) || value <= 0) return false
  return value <= MOBILE_MAX_WIDTH
}

export function shouldTrackFieldVisibility({ enabled, viewportWidth } = {}) {
  return Boolean(enabled) && isMobileViewport(viewportWidth)
}

// Returns true when the field is wholly/partly outside the currently visible
// viewport region — i.e. its lower edge is hidden behind the keyboard, or it has
// been scrolled above the top of the visible area.
export function isFieldHiddenByKeyboard({
  fieldTop,
  fieldBottom,
  viewportOffsetTop = 0,
  viewportHeight,
  margin = 0,
} = {}) {
  const height = Number(viewportHeight)
  if (!Number.isFinite(height) || height <= 0) return false

  const top = Number(viewportOffsetTop) || 0
  const visibleBottom = top + height

  if (Number.isFinite(fieldBottom) && fieldBottom + margin > visibleBottom) {
    return true
  }
  if (Number.isFinite(fieldTop) && fieldTop - margin < top) {
    return true
  }
  return false
}
