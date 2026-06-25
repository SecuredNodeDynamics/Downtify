import { ref } from 'vue'

import monitorAPI from './monitor.js'

const monitoredArtists = ref([])
const monitoredArtistMap = ref(new Map())
let loadPromise = null
let lastRefreshAt = 0

const REFRESH_TTL_MS = 60_000

export { monitoredArtists, monitoredArtistMap }

export function normalizeMonitoredArtistName(value) {
  return String(value || '')
    .trim()
    .toLocaleLowerCase()
}

function rebuildMonitoredArtistMap(items) {
  const map = new Map()
  for (const item of items || []) {
    if (item?.kind !== 'artist') continue
    const key = normalizeMonitoredArtistName(item.name)
    if (key) map.set(key, item)
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

export async function refreshMonitoredArtists({ force = false } = {}) {
  const now = Date.now()
  if (
    !force &&
    monitoredArtists.value.length > 0 &&
    now - lastRefreshAt < REFRESH_TTL_MS
  ) {
    return
  }
  if (loadPromise) return loadPromise

  loadPromise = monitorAPI
    .listMonitoredPlaylists()
    .then((res) => {
      applyMonitoredArtists(res.data)
      lastRefreshAt = Date.now()
      if (res.refresh) {
        res.refresh
          .then((fresh) => {
            applyMonitoredArtists(fresh.data)
            lastRefreshAt = Date.now()
          })
          .catch(() => {})
      }
    })
    .catch(() => {
      applyMonitoredArtists([])
    })
    .finally(() => {
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
  }
}
