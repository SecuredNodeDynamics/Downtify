let cachedPaths = null
let cachedLibraryItems = null
let cachedServerKey = ''
let prefetchPromise = null
let backgroundRefreshPromise = null
let lastBackgroundRefreshAt = 0

const PERSIST_KEY = 'downtify-library-cache-v1'
const PERSIST_MAX_AGE_MS = 24 * 60 * 60 * 1000
export const LIBRARY_BACKGROUND_REFRESH_MS = 30_000

export function getCachedLibraryPaths() {
  return cachedPaths ? [...cachedPaths] : null
}

export function getCachedLibraryItems() {
  return cachedLibraryItems ? [...cachedLibraryItems] : null
}

export function getLibraryServerKey() {
  return cachedServerKey
}

export function setLibrarySessionPaths(paths) {
  cachedPaths = Array.isArray(paths) ? [...paths] : []
}

export function setLibrarySessionItems(items) {
  cachedLibraryItems = Array.isArray(items) ? [...items] : []
}

export function setLibrarySessionCache(
  paths,
  items = undefined,
  serverKey = ''
) {
  if (serverKey) {
    cachedServerKey = serverKey
  }
  setLibrarySessionPaths(paths)
  if (items !== undefined) {
    setLibrarySessionItems(items)
  }
}

export function clearLibrarySessionCache() {
  cachedPaths = null
  cachedLibraryItems = null
  cachedServerKey = ''
}

export function resetLibraryPrefetch() {
  prefetchPromise = null
  backgroundRefreshPromise = null
  lastBackgroundRefreshAt = 0
}

export function getLibraryPrefetchPromise() {
  return prefetchPromise
}

function normalizeLibraryPayload(items) {
  return (items || [])
    .map((item) => ({
      file: String(item?.file || '').trim(),
      title: String(item?.title || '').trim(),
      artist: String(item?.artist || '').trim(),
      album: String(item?.album || '').trim(),
      genre: String(item?.genre || '').trim(),
      browse_genre: String(item?.browse_genre || item?.genre || '').trim(),
    }))
    .filter((item) => item.file)
}

export function loadPersistedLibrary(serverKey = '') {
  if (typeof localStorage === 'undefined') return null

  try {
    const raw = localStorage.getItem(PERSIST_KEY)
    if (!raw) return null

    const payload = JSON.parse(raw)
    if (!payload || !Array.isArray(payload.items) || !payload.items.length) {
      return null
    }
    if (serverKey && payload.serverKey && payload.serverKey !== serverKey) {
      return null
    }
    if (Date.now() - Number(payload.savedAt || 0) > PERSIST_MAX_AGE_MS) {
      return null
    }

    const items = normalizeLibraryPayload(payload.items)
    if (!items.length) return null

    return {
      paths: items.map((item) => item.file),
      items,
      serverKey: payload.serverKey || serverKey,
    }
  } catch {
    return null
  }
}

export function persistLibraryCache(paths, items, serverKey = '') {
  if (typeof localStorage === 'undefined') return

  const normalized = normalizeLibraryPayload(items)
  if (!normalized.length) return

  try {
    localStorage.setItem(
      PERSIST_KEY,
      JSON.stringify({
        savedAt: Date.now(),
        serverKey: serverKey || cachedServerKey,
        paths: Array.isArray(paths)
          ? paths
          : normalized.map((item) => item.file),
        items: normalized,
      })
    )
  } catch {
    // Ignore quota errors; in-memory cache still helps during the session.
  }
}

export function hydrateLibraryFromPersistence(serverKey = '') {
  const persisted = loadPersistedLibrary(serverKey)
  if (!persisted) return false

  setLibrarySessionCache(persisted.paths, persisted.items, persisted.serverKey)
  return true
}

export function getInitialLibrarySnapshot(serverKey = '') {
  if (!getCachedLibraryItems()?.length) {
    hydrateLibraryFromPersistence(serverKey)
  }

  const items = getCachedLibraryItems() || []
  const paths = getCachedLibraryPaths() || items.map((item) => item.file)
  return {
    items: [...items],
    paths: [...paths],
    ready: paths.length > 0,
  }
}

export function applyLibrarySnapshot(items, serverKey = '') {
  const normalized = normalizeLibraryPayload(items)
  if (!normalized.length) {
    return []
  }

  const paths = normalized.map((item) => item.file)
  setLibrarySessionCache(paths, normalized, serverKey)
  persistLibraryCache(paths, normalized, serverKey)
  return normalized
}

export function startLibraryPrefetch(fetchLibrary, serverKey = '') {
  if (!fetchLibrary) return null
  if (prefetchPromise) return prefetchPromise

  if (!getCachedLibraryItems()?.length) {
    hydrateLibraryFromPersistence(serverKey)
  }

  prefetchPromise = Promise.resolve()
    .then(() => fetchLibrary())
    .then((items) => applyLibrarySnapshot(items, serverKey))
    .catch(() => getCachedLibraryItems() || [])

  return prefetchPromise
}

export async function fetchLibraryItems(
  fetchLibrary,
  { preferPrefetch = true } = {}
) {
  if (preferPrefetch) {
    const pending = getLibraryPrefetchPromise()
    if (pending) {
      try {
        const items = await pending
        if (items?.length) return items
      } catch {
        // Fall through to a direct fetch below.
      }
    }
  }

  const items = await fetchLibrary()
  return applyLibrarySnapshot(items)
}

export function refreshLibraryInBackground(
  fetchLibrary,
  {
    serverKey = '',
    force = false,
    minIntervalMs = LIBRARY_BACKGROUND_REFRESH_MS,
  } = {}
) {
  if (!fetchLibrary) return Promise.resolve(getCachedLibraryItems() || [])

  const now = Date.now()
  if (
    !force &&
    backgroundRefreshPromise === null &&
    now - lastBackgroundRefreshAt < minIntervalMs
  ) {
    return Promise.resolve(getCachedLibraryItems() || [])
  }

  if (backgroundRefreshPromise) {
    return backgroundRefreshPromise
  }

  backgroundRefreshPromise = fetchLibraryItems(fetchLibrary, {
    preferPrefetch: false,
  })
    .then((items) => {
      lastBackgroundRefreshAt = Date.now()
      return items
    })
    .catch(() => getCachedLibraryItems() || [])
    .finally(() => {
      backgroundRefreshPromise = null
    })

  return backgroundRefreshPromise
}
