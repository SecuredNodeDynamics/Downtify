let cachedPaths = null
let cachedLibraryItems = null

export function getCachedLibraryPaths() {
  return cachedPaths ? [...cachedPaths] : null
}

export function getCachedLibraryItems() {
  return cachedLibraryItems ? [...cachedLibraryItems] : null
}

export function setLibrarySessionPaths(paths) {
  cachedPaths = Array.isArray(paths) ? [...paths] : []
}

export function setLibrarySessionItems(items) {
  cachedLibraryItems = Array.isArray(items) ? [...items] : []
}

export function setLibrarySessionCache(paths, items = undefined) {
  setLibrarySessionPaths(paths)
  if (items !== undefined) {
    setLibrarySessionItems(items)
  }
}

export function clearLibrarySessionCache() {
  cachedPaths = null
  cachedLibraryItems = null
}
