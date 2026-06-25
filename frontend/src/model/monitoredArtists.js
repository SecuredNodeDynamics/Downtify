import { ref } from 'vue'

import monitorAPI from './monitor.js'

const monitoredArtists = ref([])
let loadPromise = null

export { monitoredArtists }

export function normalizeMonitoredArtistName(value) {
  return String(value || '')
    .trim()
    .toLocaleLowerCase()
}

export function findMonitoredArtist(artistName) {
  const target = normalizeMonitoredArtistName(artistName)
  if (!target) return null
  return (
    monitoredArtists.value.find(
      (item) =>
        item.kind === 'artist' && normalizeMonitoredArtistName(item.name) === target
    ) || null
  )
}

export async function refreshMonitoredArtists() {
  if (loadPromise) return loadPromise

  loadPromise = monitorAPI
    .listMonitoredPlaylists()
    .then((res) => {
      monitoredArtists.value = Array.isArray(res.data) ? res.data : []
      if (res.refresh) {
        res.refresh
          .then((fresh) => {
            monitoredArtists.value = Array.isArray(fresh.data) ? fresh.data : []
          })
          .catch(() => {})
      }
    })
    .catch(() => {
      monitoredArtists.value = []
    })
    .finally(() => {
      loadPromise = null
    })

  return loadPromise
}

export function useMonitoredArtists() {
  return {
    monitoredArtists,
    findMonitoredArtist,
    refreshMonitoredArtists,
  }
}
