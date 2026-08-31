export function libraryGridColumns(width = 0) {
  if (width >= 1024) return 4
  if (width >= 640) return 3
  return 2
}

export function virtualBrowseWindow({
  count,
  columns = 1,
  itemSize = 76,
  scrollTop = 0,
  viewportHeight = 600,
  overscanRows = 3,
} = {}) {
  const total = Math.max(0, Number(count) || 0)
  const cols = Math.max(1, Number(columns) || 1)
  const size = Math.max(1, Number(itemSize) || 1)
  const rows = Math.ceil(total / cols) || 0
  const startRow = Math.max(
    0,
    Math.floor((scrollTop || 0) / size) - overscanRows
  )
  const visibleRows = Math.ceil((viewportHeight || 0) / size) + overscanRows * 2
  const endRow = Math.min(rows, startRow + Math.max(visibleRows, 1))
  return {
    start: Math.min(total, startRow * cols),
    end: Math.min(total, endRow * cols),
    padTop: startRow * size,
    padBottom: Math.max(0, (rows - endRow) * size),
  }
}
