export function settingsTabsNeedMenu({ tabWidths, gap, available }) {
  const widths = (tabWidths || []).map((value) => Number(value) || 0)
  if (widths.length <= 1) return false
  const spacing = Math.max(0, Number(gap) || 0)
  const limit = Number(available)
  if (!Number.isFinite(limit) || limit <= 0) return false
  const total =
    widths.reduce((sum, width) => sum + width, 0) +
    spacing * (widths.length - 1)
  return total > limit + 0.5
}

export function countOverflowSettingsTabs(options) {
  return settingsTabsNeedMenu(options) ? 1 : 0
}
