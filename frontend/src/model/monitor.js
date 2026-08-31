import axios from 'axios'

import {
  authHeaders,
  authStatus,
  markAuthUnauthorized,
  shouldMarkAuthUnauthorized,
} from './authSession.js'
import {
  capacitorAxiosAdapter,
  shouldUseNativeHttpAdapter,
} from './nativeHttp.js'
import { loadProfileBundle, storeProfileBundle } from './profileSync.js'
import { buildApiBaseUrl, getServerConfig } from './serverConnection.js'

const API = axios.create()
const artistLookupCache = new Map()
const ARTIST_LOOKUP_TTL_MS = 10 * 60 * 1000

API.interceptors.request.use((config) => {
  config.baseURL = buildApiBaseUrl(getServerConfig())
  const headers = authHeaders()
  if (headers.Authorization) {
    config.headers = config.headers || {}
    config.headers.Authorization = headers.Authorization
  }
  if (shouldUseNativeHttpAdapter(config)) {
    config.adapter = capacitorAxiosAdapter
  }
  return config
})

API.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    if (shouldMarkAuthUnauthorized(status, error?.config)) {
      markAuthUnauthorized()
    }
    return Promise.reject(error)
  }
)

export function monitorListCacheKey() {
  const base = String(buildApiBaseUrl(getServerConfig()) || '').replace(
    /\/+$/,
    ''
  )
  const user = authStatus.value.user
  const who = user
    ? `${user.id || 'id'}:${String(user.username || '').toLowerCase()}`
    : 'anon'
  return `downtify.monitor.playlists:${base}:${who}`
}

function readCachedPlaylists() {
  try {
    const raw = sessionStorage.getItem(monitorListCacheKey())
    if (!raw) return null
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : null
  } catch {
    return null
  }
}

function persistUserMonitorBundle(items, { allowEmpty = false } = {}) {
  const user = authStatus.value.user
  if (!user) return
  const existing = loadProfileBundle(user) || {}
  const existingMonitors = Array.isArray(existing.monitors)
    ? existing.monitors
    : []
  const incoming = items || []
  if (!allowEmpty && incoming.length === 0 && existingMonitors.length > 0) {
    return
  }
  storeProfileBundle({
    profile_key: user.profile_key || existing.profile_key || '',
    username: user.username || existing.username || '',
    display_name:
      user.display_name || existing.display_name || user.username || '',
    monitors: incoming.map((item) => ({
      spotify_id: item?.spotify_id,
      name: item?.name,
      url: item?.url,
      kind: item?.kind,
      interval_minutes: item?.interval_minutes,
      enabled: item?.enabled,
      image_url: item?.image_url,
    })),
    groups: Array.isArray(existing.groups) ? existing.groups : [],
  })
}

function writeCachedPlaylists(items, { allowEmptyBundle = false } = {}) {
  const deduped = dedupeMonitoredPlaylists(items)
  try {
    sessionStorage.setItem(monitorListCacheKey(), JSON.stringify(deduped))
  } catch {
    // Ignore quota or privacy errors.
  }
  persistUserMonitorBundle(deduped, { allowEmpty: allowEmptyBundle })
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
  const key = `${String(artistName || '')
    .trim()
    .toLocaleLowerCase()}:${limit}`
  const cached = artistLookupCache.get(key)
  if (cached && Date.now() - cached.createdAt < ARTIST_LOOKUP_TTL_MS) {
    return cached.promise
  }
  const promise = API.get('/api/monitor/artists/lookup', {
    params: { artist: artistName, limit },
    timeout: 20000,
  }).catch((error) => {
    artistLookupCache.delete(key)
    throw error
  })
  artistLookupCache.set(key, { createdAt: Date.now(), promise })
  return promise
}

function searchMonitorTargets(query, kind = 'artist', limit = 6) {
  return API.get('/api/monitor/search', {
    params: { q: query, kind, limit },
    timeout: 30000,
  })
}

function addMonitoredPlaylist(url, intervalMinutes = 60, kind = 'playlist') {
  return API.post('/api/monitor/playlists', {
    url,
    interval_minutes: intervalMinutes,
    kind,
  }).then((res) => {
    const cached = readCachedPlaylists() || []
    writeCachedPlaylists(
      [res.data, ...cached.filter((item) => item.id !== res.data.id)],
      { allowEmptyBundle: true }
    )
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
      cached.map((item) => (item.id === id ? { ...item, ...res.data } : item)),
      { allowEmptyBundle: true }
    )
    return res
  })
}

function deleteMonitoredPlaylist(id) {
  return API.delete(`/api/monitor/playlists/${id}`).then((res) => {
    const cached = readCachedPlaylists() || []
    writeCachedPlaylists(
      cached.filter((item) => item.id !== id),
      { allowEmptyBundle: true }
    )
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
  searchMonitorTargets,
  addMonitoredPlaylist,
  updateMonitoredPlaylist,
  deleteMonitoredPlaylist,
  checkMonitoredPlaylist,
}
