// small file used as placeholder/settings for API calls via axios to server-side
import axios from 'axios' // used to connect to server backend in ./server folder
import {
  buildApiBaseUrl,
  buildWsUrl,
  getServerConfig,
  isCapacitorNative,
  needsServerConnection,
  usesCustomServerUrl,
} from './serverConnection.js'
import { libraryCoverFolders } from './library.js'
import {
  persistLibraryCache,
  refreshLibraryInBackground as refreshLibrarySession,
  resetLibraryPrefetch,
  startLibraryPrefetch,
} from './librarySession.js'
import { preloadCoverSourcesBatch } from './imageLoader.js'
import {
  getBundledAppVersion,
  getInstalledClientVersionSync,
  resolveNativeInstalledVersion,
  sanitizeStoredVersions,
  writeCachedServerVersion,
} from './appVersion.js'

import { v4 as uuidv4 } from 'uuid'

const API = axios.create()

API.interceptors.request.use((config) => {
  config.baseURL = buildApiBaseUrl(getServerConfig())
  return config
})

const sessionID = uuidv4()

const SEMVER = /^\d+\.\d+\.\d+$/

let wsConnection = null
let wsMessageHandler = null
let wsErrorHandler = null

function isValidVersion(value) {
  return typeof value === 'string' && SEMVER.test(value.trim())
}

function isJsonObject(value) {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value)
}

function sanitizeStoredVersion() {
  sanitizeStoredVersions()
}

function attachWebSocketHandlers(socket) {
  socket.onopen = (event) => {
    console.log('websocket connection opened', event)
  }
  socket.onmessage = (event) => {
    try {
      wsMessageHandler?.(event)
    } catch (error) {
      console.warn('WebSocket message handler failed:', error)
    }
  }
  socket.onerror = (event) => {
    wsErrorHandler?.(event)
  }
}

function ensureWebSocket() {
  if (needsServerConnection()) {
    if (wsConnection) {
      wsConnection.close()
      wsConnection = null
    }
    return null
  }

  const url = buildWsUrl(getServerConfig(), sessionID)
  if (wsConnection && wsConnection.url === url) {
    return wsConnection
  }

  if (wsConnection) {
    wsConnection.close()
  }

  try {
    wsConnection = new WebSocket(url)
    attachWebSocketHandlers(wsConnection)
  } catch (error) {
    console.warn('Could not open websocket:', error)
    wsConnection = null
  }
  return wsConnection
}

function getVersion() {
  if (needsServerConnection()) return

  API.get('/api/version')
    .then((res) => {
      const version = String(res.data ?? '').trim()
      if (!isValidVersion(version)) {
        console.warn(
          'Ignoring invalid /api/version response (is the backend running?)'
        )
        return
      }
      if (isCapacitorNative()) {
        writeCachedServerVersion(version)
        prefetchLibrary()
        return
      }
      const prevItem = localStorage.getItem('version')
      console.log('Backend version: ', version)
      localStorage.setItem('version', version)
      if (prevItem != version) {
        location.reload()
      }
      prefetchLibrary()
    })
    .catch((error) => {
      console.error(error)
      console.log('Error getting version, using 0')
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem('version', '0.0.0')
      }
    })
}

sanitizeStoredVersion()
if (!needsServerConnection()) {
  if (isCapacitorNative()) {
    resolveNativeInstalledVersion()
  }
  getVersion()
  ensureWebSocket()
  prefetchLibrary()
}

function search(query) {
  return API.get('/api/songs/search', { params: { query } })
}

function open(songURL) {
  return API.get('/api/song/url', { params: { url: songURL } })
}

function openYoutubeAlbum(browseId) {
  return API.get('/api/album/youtube', { params: { browse_id: browseId } })
}

function download(songURL) {
  const url = typeof songURL === 'string' ? songURL : songURL.url
  const hints = typeof songURL === 'string' ? undefined : songURL
  return API.post('/api/download/url', hints, {
    params: { url, client_id: sessionID },
  })
}

function downloadBatch(payload) {
  return API.post('/api/download/batch', payload)
}

function preview(songURL) {
  const url = typeof songURL === 'string' ? songURL : songURL.url
  return API.get('/api/preview', { params: { url } })
}

function audioPreview(song) {
  return API.post('/api/preview/audio', song)
}

function check_for_update(refresh = false) {
  return API.get('/api/check_update', { params: { refresh } })
}

function updateApp() {
  return API.post('/api/update')
}

function getAppVersion() {
  return API.get('/api/version')
}

function getHealth() {
  return API.get('/api/health')
}

function startMetadataScan(limit = 100, reset = false, scanAll = false) {
  return API.post('/api/metadata/scan', { limit, reset, all: scanAll })
}

function getMetadataScanStatus() {
  return API.get('/api/metadata/scan/status')
}

function applyMetadata(file) {
  return API.post('/api/metadata/apply', { file })
}

function scanArtistImages(limit = 50, scanAll = false, reset = false) {
  return API.post('/api/metadata/artist-images/scan', {
    limit,
    all: scanAll,
    reset,
  })
}

function getArtistImageScanStatus() {
  return API.get('/api/metadata/artist-images/status')
}

function getArtistImageOptions(item) {
  return API.get('/api/metadata/artist-images/options', {
    params: {
      artist: item.artist || item.name,
      file: item.file || '',
      folder: item.folder || '',
      jellyfin_artist_id: item.jellyfin_artist_id || '',
    },
    timeout: 120000,
  })
}

function applyArtistImage(item, selection = {}) {
  return API.post(
    '/api/metadata/artist-images/apply',
    {
      file: item.file,
      artist: item.artist || item.name,
      artist_id: item.artist_id,
      folder: item.folder,
      jellyfin_artist_id:
        selection.jellyfin_artist_id || item.jellyfin_artist_id || '',
      image_url: selection.image_url || '',
      selected_option_id: selection.id || '',
    },
    { timeout: 120000 }
  )
}

function getRepairLog(limit = 25) {
  return API.get('/api/metadata/repair-log', { params: { limit } })
}

function encodePath(fileName) {
  // Encode each path segment individually so '/' separators survive —
  // playlist downloads land under '<playlist>/<song>.mp3' and we need
  // the URL to hit '/downloads/<playlist>/<song>.mp3' literally.
  return String(fileName || '')
    .split('/')
    .map(encodeURIComponent)
    .join('/')
}

function downloadFileURL(fileName) {
  const path = `/downloads/${encodePath(fileName)}`
  if (isCapacitorNative() || usesCustomServerUrl()) {
    return `${buildApiBaseUrl(getServerConfig())}${path}`
  }
  return path
}

function coverFileURL(fileName) {
  const file = String(fileName || '').trim()
  if (!file) return ''
  return apiAssetUrl(`/cover?${new URLSearchParams({ file })}`)
}

function coverFolderURL(folderPath) {
  const folder = String(folderPath || '').trim()
  if (!folder) return ''
  return apiAssetUrl(
    `/api/metadata/artist-images/folder-preview?${new URLSearchParams({
      folder,
    })}`
  )
}

function coverUrlsForLibraryFile(fileName) {
  const urls = [coverFileURL(fileName)]
  for (const folder of libraryCoverFolders(fileName)) {
    urls.push(coverFolderURL(folder))
  }
  return [...new Set(urls.filter(Boolean))]
}

function coverFallbackUrls(fileName) {
  return coverUrlsForLibraryFile(fileName).slice(1)
}

const EMPTY_COVER_SOURCES = Object.freeze({
  src: '',
  fallbacks: Object.freeze([]),
})

const coverSourcesCache = new Map()

function coverSourcesForFile(fileName) {
  const file = String(fileName || '').trim()
  if (!file) return EMPTY_COVER_SOURCES

  const cached = coverSourcesCache.get(file)
  if (cached) return cached

  const urls = coverUrlsForLibraryFile(file)
  const entry = Object.freeze({
    src: urls[0] || '',
    fallbacks: Object.freeze(urls.slice(1)),
  })
  coverSourcesCache.set(file, entry)
  return entry
}

function coverSourcesForArtist(artistName, previewFiles = []) {
  const name = String(artistName || '').trim()
  const files = (previewFiles || [])
    .map((file) => String(file || '').trim())
    .filter(Boolean)
  const cacheKey = `artist:${name}\0${files.join('\0')}`
  const cached = coverSourcesCache.get(cacheKey)
  if (cached) return cached

  const urls = []
  if (name) urls.push(coverFolderURL(name))
  for (const file of files) {
    urls.push(...coverUrlsForLibraryFile(file))
  }
  const deduped = [...new Set(urls.filter(Boolean))]
  const entry = Object.freeze({
    src: deduped[0] || '',
    fallbacks: Object.freeze(deduped.slice(1)),
  })
  coverSourcesCache.set(cacheKey, entry)
  return entry
}

function clearCoverSourcesCache() {
  coverSourcesCache.clear()
}

function warmLibraryCovers(items = []) {
  const entries = []
  const seenArtists = new Set()

  for (const item of items) {
    const artist = String(item?.artist || '').trim()
    const file = String(item?.file || '').trim()
    if (!artist || !file || seenArtists.has(artist)) continue
    seenArtists.add(artist)
    entries.push(coverSourcesForArtist(artist, [file]))
    if (seenArtists.size >= 24) break
  }

  for (const item of items.slice(0, 48)) {
    const file = String(item?.file || '').trim()
    if (file) entries.push(coverSourcesForFile(file))
  }

  preloadCoverSourcesBatch(entries, { limit: 96 })
}

const CDN_IMAGE_HOST_SUFFIXES = [
  'scdn.co',
  'spotifycdn.com',
  'googleusercontent.com',
  'ggpht.com',
  'ytimg.com',
  'mzstatic.com',
]

function isCdnImageUrl(url) {
  try {
    const host = new URL(url).hostname.toLowerCase()
    return CDN_IMAGE_HOST_SUFFIXES.some(
      (suffix) => host === suffix || host.endsWith(`.${suffix}`)
    )
  } catch {
    return false
  }
}

function shouldProxyRemoteImage(url) {
  if (isCdnImageUrl(url)) return true
  if (!isCapacitorNative()) return false
  try {
    const target = new URL(url)
    const server = new URL(buildApiBaseUrl(getServerConfig()))
    if (target.origin === server.origin) return false
    return target.protocol === 'http:' || target.protocol === 'https:'
  } catch {
    return false
  }
}

function mediaUrl(src) {
  const value = String(src || '').trim()
  if (!value) return ''
  let resolved = value
  if (/^https?:\/\//i.test(value)) {
    resolved = value
  } else if (value.startsWith('//')) {
    resolved = `${getServerConfig().PROTOCOL}${value}`
  } else {
    return apiAssetUrl(value)
  }
  if (shouldProxyRemoteImage(resolved)) {
    const base = buildApiBaseUrl(getServerConfig())
    return `${base}/api/image-proxy?${new URLSearchParams({ url: resolved })}`
  }
  return resolved
}

function apiAssetUrl(path) {
  const value = String(path || '').trim()
  if (!value) return ''
  if (/^https?:\/\//i.test(value)) return value
  if (isCapacitorNative() || usesCustomServerUrl()) {
    return `${buildApiBaseUrl(getServerConfig())}${
      value.startsWith('/') ? value : `/${value}`
    }`
  }
  return value.startsWith('/') ? value : `/${value}`
}

function listDownloads() {
  return API.get('/list')
}

function getLibraryFiles() {
  return API.get('/api/library/files')
}

function getLibraryGenresStatus() {
  return API.get('/api/library/genres/status')
}

function deleteDownload(file) {
  return API.delete('/delete', { params: { file } })
}

function writePlaylistM3u(payload) {
  return API.post('/api/playlist/m3u', payload)
}

function getQueue() {
  return API.get('/api/queue')
}

function removeQueueItem(songId) {
  return API.delete('/api/queue/item', { params: { song_id: songId } })
}

function clearQueue() {
  return API.delete('/api/queue')
}

function getHistory(limit = 500) {
  return API.get('/api/history', { params: { limit } })
}

function retryHistoryItem(historyId) {
  return API.post(`/api/history/${historyId}/retry`)
}

function clearHistory() {
  return API.delete('/api/history')
}

function getSettings() {
  return API.get('/api/settings', { params: { client_id: sessionID } })
}
function setSettings(settings) {
  return API.post('/api/settings/update', settings, {
    params: { client_id: sessionID },
  })
}

function getJellyfinLibraries(jellyfinUrl, jellyfinApiKey) {
  return API.get('/api/jellyfin/libraries', {
    params: { jellyfin_url: jellyfinUrl, jellyfin_api_key: jellyfinApiKey },
  })
}

function getJellyfinDebug(jellyfinUrl, jellyfinApiKey) {
  return API.get('/api/jellyfin/debug', {
    params: { jellyfin_url: jellyfinUrl, jellyfin_api_key: jellyfinApiKey },
  })
}

function reconcileJellyfinArtists() {
  return API.get('/api/jellyfin/artists/reconcile')
}

function refreshJellyfinLibrary() {
  return API.post('/api/jellyfin/refresh')
}

function ws_onmessage(fn) {
  wsMessageHandler = fn
  ensureWebSocket()
  return fn
}
function ws_onerror(fn) {
  wsErrorHandler = fn
  ensureWebSocket()
  return fn
}

function libraryServerKey() {
  return buildApiBaseUrl(getServerConfig())
}

async function fetchLibraryItemsFromApi() {
  const res = await getLibraryFiles()
  return Array.isArray(res.data) ? res.data : []
}

function prefetchLibrary() {
  const promise = startLibraryPrefetch(
    fetchLibraryItemsFromApi,
    libraryServerKey()
  )
  promise?.then((items) => {
    if (items?.length) warmLibraryCovers(items)
    return items
  })
  return promise
}

function refreshLibraryInBackground(force = false) {
  return refreshLibrarySession(fetchLibraryItemsFromApi, {
    serverKey: libraryServerKey(),
    force,
  }).then((items) => {
    if (items?.length) warmLibraryCovers(items)
    return items
  })
}

function reconnectBackend() {
  resetLibraryPrefetch()
  getVersion()
  ensureWebSocket()
  prefetchLibrary()
}

export function isHealthPayload(data) {
  return (
    isJsonObject(data) &&
    typeof data.status === 'string' &&
    isJsonObject(data.tools) &&
    isJsonObject(data.queue) &&
    isJsonObject(data.history)
  )
}

export default {
  search,
  open,
  openYoutubeAlbum,
  download,
  downloadBatch,
  preview,
  audioPreview,
  downloadFileURL,
  coverFileURL,
  coverFolderURL,
  coverUrlsForLibraryFile,
  coverFallbackUrls,
  coverSourcesForFile,
  coverSourcesForArtist,
  clearCoverSourcesCache,
  warmLibraryCovers,
  refreshLibraryInBackground,
  libraryServerKey,
  apiAssetUrl,
  mediaUrl,
  listDownloads,
  getLibraryFiles,
  getLibraryGenresStatus,
  deleteDownload,
  writePlaylistM3u,
  getQueue,
  removeQueueItem,
  clearQueue,
  getHistory,
  retryHistoryItem,
  clearHistory,
  getSettings,
  setSettings,
  getJellyfinLibraries,
  getJellyfinDebug,
  reconcileJellyfinArtists,
  refreshJellyfinLibrary,
  check_for_update,
  updateApp,
  getAppVersion,
  getHealth,
  startMetadataScan,
  getMetadataScanStatus,
  applyMetadata,
  scanArtistImages,
  getArtistImageScanStatus,
  getArtistImageOptions,
  applyArtistImage,
  getRepairLog,
  ws_onmessage,
  ws_onerror,
  getVersion,
  reconnectBackend,
  isHealthPayload,
}
