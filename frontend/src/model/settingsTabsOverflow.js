export function countOverflowSettingsTabs({
  tabWidths,
  moreWidth,
  gap,
  available,
}) {
  const widths = (tabWidths || []).map((value) => Number(value) || 0)
  const count = widths.length
  if (count <= 1) return 0
  const spacing = Math.max(0, Number(gap) || 0)
  const menu = Math.max(0, Number(moreWidth) || 0)
  const limit = Number(available)
  if (!Number.isFinite(limit) || limit <= 0) return 0

  const rowWidth = (visible) => {
    const shown = widths.slice(0, visible)
    let total = shown.reduce((sum, width) => sum + width, 0)
    if (shown.length > 1) total += spacing * (shown.length - 1)
    if (visible < count) {
      total += (shown.length ? spacing : 0) + menu
    }
    return total
  }

  let visible = count
  while (visible > 1 && rowWidth(visible) > limit + 0.5) {
    visible -= 1
  }
  return count - visible
}
