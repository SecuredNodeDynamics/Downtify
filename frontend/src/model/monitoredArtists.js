import { ref } from 'vue'

import monitorAPI from './monitor.js'

const monitoredArtists = ref([])
const monitoredArtistMap = ref(new Map())
const ALIAS_STORAGE_KEY = 'downtify.monitor.artist-aliases'

let loadPromise = null
let lastRefreshAt = 0

const REFRESH_TTL_MS = 60_000

export { monitoredArtists, monitoredArtistMap }

export function normalizeMonitoredArtistName(value) {
  return String(value || '')
    .trim()
    .toLocaleLowerCase()
}

function readArtistAliases() {
  try {
    const raw = sessionStorage.getItem(ALIAS_STORAGE_KEY)
    if (!raw) return {}
    const parsed = JSON.parse(raw)
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

function writeArtistAlias(libraryArtistName, monitoredArtistName) {
  const libraryKey = normalizeMonitoredArtistName(libraryArtistName)
  const monitoredKey = normalizeMonitoredArtistName(monitoredArtistName)
  if (!libraryKey || !monitoredKey) return

  const aliases = readArtistAliases()
  aliases[libraryKey] = monitoredKey
  try {
    sessionStorage.setItem(ALIAS_STORAGE_KEY, JSON.stringify(aliases))
  } catch {
    // Ignore quota or privacy errors.
  }
}

function rebuildMonitoredArtistMap(items) {
  const map = new Map()
  const aliases = readArtistAliases()

  for (const item of items || []) {
    if (item?.kind !== 'artist') continue
    const key = normalizeMonitoredArtistName(item.name)
    if (key) map.set(key, item)
  }

  for (const [libraryKey, monitoredKey] of Object.entries(aliases)) {
    if (map.has(libraryKey)) continue
    const item = map.get(monitoredKey)
    if (item) map.set(libraryKey, item)
  }

  monitoredArtistMap.value = map
}

export function findMonitoredArtist(artistName) {
  const target = normalizeMonitoredArtistName(artistName)
  if (!target) return null
  return monitoredArtistMap.value.get(target) || null
}

function applyMonitoredArtists(items) {
  monitoredArtists.value = Array.isArray(items) ? items : []
  rebuildMonitoredArtistMap(monitoredArtists.value)
}

export function upsertMonitoredArtist(item, libraryArtistName = '') {
  if (!item || item.kind !== 'artist') return

  const items = [...monitoredArtists.value]
  const index = items.findIndex((entry) => entry.id === item.id)
  if (index >= 0) items[index] = item
  else items.unshift(item)

  applyMonitoredArtists(items)
  lastRefreshAt = Date.now()

  if (libraryArtistName) {
    writeArtistAlias(libraryArtistName, item.name)
    rebuildMonitoredArtistMap(items)
  }
}

export async function refreshMonitoredArtists({ force = false } = {}) {
  const now = Date.now()
  if (
    !force &&
    monitoredArtists.value.length > 0 &&
    now - lastRefreshAt < REFRESH_TTL_MS
  ) {
    return
  }

  if (force) {
    loadPromise = null
  } else if (loadPromise) {
    return loadPromise
  }

  loadPromise = (async () => {
    try {
      const res = await monitorAPI.listMonitoredPlaylists({
        useCache: !force,
      })

      if (force && res.refresh) {
        const fresh = await res.refresh
        applyMonitoredArtists(fresh.data)
      } else {
        applyMonitoredArtists(res.data)
        if (res.refresh) {
          res.refresh
            .then((fresh) => {
              applyMonitoredArtists(fresh.data)
              lastRefreshAt = Date.now()
            })
            .catch(() => {})
        }
      }

      lastRefreshAt = Date.now()
    } catch {
      if (!force) applyMonitoredArtists([])
    }
  })().finally(() => {
    loadPromise = null
  })

  return loadPromise
}

export function useMonitoredArtists() {
  return {
    monitoredArtists,
    monitoredArtistMap,
    findMonitoredArtist,
    refreshMonitoredArtists,
    upsertMonitoredArtist,
  }
}
