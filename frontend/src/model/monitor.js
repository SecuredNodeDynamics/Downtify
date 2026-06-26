import axios from 'axios'
import { buildApiBaseUrl, getServerConfig } from './serverConnection.js'

const API = axios.create()
const CACHE_KEY = 'downtify.monitor.playlists'

API.interceptors.request.use((config) => {
  config.baseURL = buildApiBaseUrl(getServerConfig())
  return config
})

function readCachedPlaylists() {
  try {
    const raw = sessionStorage.getItem(CACHE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : null
  } catch {
    return null
  }
}

function writeCachedPlaylists(items) {
  try {
    sessionStorage.setItem(
      CACHE_KEY,
      JSON.stringify(dedupeMonitoredPlaylists(items))
    )
  } catch {
    // Ignore quota or privacy errors.
  }
}

function normalizeMonitoredArtistName(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
}

function dedupeMonitoredPlaylists(items) {
  const seenIds = new Set()
  const seenArtistNames = new Set()
  const deduped = []

  for (const item of items || []) {
    if (!item || typeof item !== 'object') continue

    if (item.kind === 'artist') {
      const spotifyId = String(item.spotify_id || '').trim()
      const nameKey = normalizeMonitoredArtistName(item.name)
      if (spotifyId && seenIds.has(spotifyId)) continue
      if (nameKey && seenArtistNames.has(nameKey)) continue
      if (spotifyId) seenIds.add(spotifyId)
      if (nameKey) seenArtistNames.add(nameKey)
    }

    deduped.push(item)
  }

  return deduped
}

function listMonitoredPlaylists({ useCache = true } = {}) {
  const liveRequest = API.get('/api/monitor/playlists', {
    timeout: 15000,
  }).then((res) => {
    writeCachedPlaylists(res.data || [])
    return {
      ...res,
      data: dedupeMonitoredPlaylists(res.data || []),
    }
  })

  const cached = useCache ? readCachedPlaylists() : null
  if (!cached) {
    return liveRequest
  }

  return Promise.resolve({
    data: dedupeMonitoredPlaylists(cached),
    fromCache: true,
    refresh: liveRequest,
  })
}

function lookupSpotifyArtists(artistName, limit = 5) {
  return API.get('/api/monitor/artists/lookup', {
    params: { artist: artistName, limit },
    timeout: 60000,
  })
}

function addMonitoredPlaylist(url, intervalMinutes = 60, kind = 'playlist') {
  return API.post('/api/monitor/playlists', {
    url,
    interval_minutes: intervalMinutes,
    kind,
  }).then((res) => {
    const cached = readCachedPlaylists() || []
    writeCachedPlaylists([
      res.data,
      ...cached.filter((item) => item.id !== res.data.id),
    ])
    return res
  })
}

function updateMonitoredPlaylist(id, updates) {
  return API.post(`/api/monitor/playlists/${id}/update`, updates, {
    timeout: 15000,
    headers: { 'Content-Type': 'application/json' },
  }).then((res) => {
    const cached = readCachedPlaylists() || []
    writeCachedPlaylists(
      cached.map((item) => (item.id === id ? { ...item, ...res.data } : item))
    )
    return res
  })
}

function deleteMonitoredPlaylist(id) {
  return API.delete(`/api/monitor/playlists/${id}`).then((res) => {
    const cached = readCachedPlaylists() || []
    writeCachedPlaylists(cached.filter((item) => item.id !== id))
    return res
  })
}

function checkMonitoredPlaylist(id) {
  return API.post(`/api/monitor/playlists/${id}/check`, null, {
    timeout: 300000,
    headers: { 'Content-Type': 'application/json' },
  })
}

export default {
  listMonitoredPlaylists,
  lookupSpotifyArtists,
  addMonitoredPlaylist,
  updateMonitoredPlaylist,
  deleteMonitoredPlaylist,
  checkMonitoredPlaylist,
}
