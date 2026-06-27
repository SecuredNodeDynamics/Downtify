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
  notifyLibraryChanged,
  persistLibraryCache,
  refreshLibraryInBackground as refreshLibrarySession,
  resetLibraryPrefetch,
  startLibraryPrefetch,
} from './librarySession.js'
import {
  invalidateArtistCoverCaches,
  preloadCoverSourcesBatch,
} from './imageLoader.js'
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

function isBrowserOnApiRoute() {
  if (typeof window === 'undefined') return false
  return /^\/api(?:\/|$)/.test(window.location?.pathname || '')
}

function reloadAppShell() {
  if (typeof window === 'undefined') return
  if (isBrowserOnApiRoute()) {
    window.location.replace('/')
    return
  }
  window.location.reload()
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
      writeCachedServerVersion(version)
      const prevItem = localStorage.getItem('version')
      console.log('Backend version: ', version)
      localStorage.setItem('version', version)
      if (isValidVersion(prevItem) && prevItem !== version) {
        reloadAppShell()
      } else if (isBrowserOnApiRoute()) {
        reloadAppShell()
      }
      prefetchLibrary()
    })
    .catch((error) => {
      console.error(error)
      console.log('Error getting version; keeping last known version')
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

// Grids and lists only ever show covers at small sizes, so request downscaled
// thumbnails by default. This dramatically cuts transfer + decode time on the
// embedded Android (loopback) backend where full-resolution embedded artwork
// (often 1000x1000+) made the library feel slow. The full-screen player asks
// for a larger size, and metadata editing uses the original (size 0).
const DEFAULT_COVER_SIZE = 320

function withCoverSize(params, size) {
  const value = Number(size)
  if (Number.isFinite(value) && value > 0) {
    params.size = String(Math.round(value))
  }
  return params
}

function coverFileURL(fileName, size = DEFAULT_COVER_SIZE) {
  const file = String(fileName || '').trim()
  if (!file) return ''
  return apiAssetUrl(
    `/cover?${new URLSearchParams(withCoverSize({ file }, size))}`
  )
}

function coverFolderURL(folderPath, size = DEFAULT_COVER_SIZE) {
  const folder = String(folderPath || '').trim()
  if (!folder) return ''
  return apiAssetUrl(
    `/api/metadata/artist-images/folder-preview?${new URLSearchParams(
      withCoverSize({ folder }, size)
    )}`
  )
}

function coverUrlsForLibraryFile(fileName, size = DEFAULT_COVER_SIZE) {
  const urls = [coverFileURL(fileName, size)]
  for (const folder of libraryCoverFolders(fileName)) {
    urls.push(coverFolderURL(folder, size))
  }
  return [...new Set(urls.filter(Boolean))]
}

function coverUrlsForGenreFile(fileName, size = DEFAULT_COVER_SIZE) {
  const urls = []
  for (const folder of libraryCoverFolders(fileName)) {
    urls.push(coverFolderURL(folder, size))
  }
  urls.push(coverFileURL(fileName, size))
  return [...new Set(urls.filter(Boolean))]
}

function coverFallbackUrls(fileName, size = DEFAULT_COVER_SIZE) {
  return coverUrlsForLibraryFile(fileName, size).slice(1)
}

const EMPTY_COVER_SOURCES = Object.freeze({
  src: '',
  fallbacks: Object.freeze([]),
})

const coverSourcesCache = new Map()

function coverSourcesForFile(fileName, size = DEFAULT_COVER_SIZE) {
  const file = String(fileName || '').trim()
  if (!file) return EMPTY_COVER_SOURCES

  const cacheKey = `${size}\0${file}`
  const cached = coverSourcesCache.get(cacheKey)
  if (cached) return cached

  const urls = coverUrlsForLibraryFile(file, size)
  const entry = Object.freeze({
    src: urls[0] || '',
    fallbacks: Object.freeze(urls.slice(1)),
  })
  coverSourcesCache.set(cacheKey, entry)
  return entry
}

function coverSourcesForGenreFile(fileName, size = DEFAULT_COVER_SIZE) {
  const file = String(fileName || '').trim()
  if (!file) return EMPTY_COVER_SOURCES

  const cacheKey = `genre:${size}\0${file}`
  const cached = coverSourcesCache.get(cacheKey)
  if (cached) return cached

  const urls = coverUrlsForGenreFile(file, size)
  const entry = Object.freeze({
    src: urls[0] || '',
    fallbacks: Object.freeze(urls.slice(1)),
  })
  coverSourcesCache.set(cacheKey, entry)
  return entry
}

function coverSourcesForArtist(
  artistName,
  previewFiles = [],
  size = DEFAULT_COVER_SIZE
) {
  const name = String(artistName || '').trim()
  const files = (previewFiles || [])
    .map((file) => String(file || '').trim())
    .filter(Boolean)
  const cacheKey = `artist:${size}\0${name}\0${files.join('\0')}`
  const cached = coverSourcesCache.get(cacheKey)
  if (cached) return cached

  const urls = []
  // Prefer a real artist photo (saved as {Artist}/{Artist}.jpg by the
  // downloader / metadata repair) so the artist tile shows a headshot rather
  // than one of the artist's album covers. Falls back to embedded album art
  // when no artist photo exists yet.
  if (name) urls.push(coverFolderURL(name, size))
  for (const file of files) {
    urls.push(...coverUrlsForLibraryFile(file, size))
  }
  const deduped = [...new Set(urls.filter(Boolean))]
  const entry = Object.freeze({
    src: deduped[0] || '',
    fallbacks: Object.freeze(deduped.slice(1)),
  })
  coverSourcesCache.set(cacheKey, entry)
  return entry
}

const NOW_PLAYING_COVER_SIZE_WEB = 640

function mergeCoverSources(primary, secondary) {
  const urls = [
    primary?.src,
    ...(primary?.fallbacks || []),
    secondary?.src,
    ...(secondary?.fallbacks || []),
  ]
    .map((url) => String(url || '').trim())
    .filter(Boolean)
  const deduped = [...new Set(urls)]
  return {
    src: deduped[0] || '',
    fallbacks: Object.freeze(deduped.slice(1)),
  }
}

/**
 * Cover URLs for the full-screen now-playing artwork. On native embedded builds
 * stick to the same 320px thumbnail size used by library grids so the hero art
 * reuses warmed cache entries and avoids unreliable 640px /cover responses.
 */
function coverSourcesForNowPlaying(fileName, { artistName = '' } = {}) {
  const file = String(fileName || '').trim()
  if (!file) return EMPTY_COVER_SOURCES

  const size = isCapacitorNative()
    ? DEFAULT_COVER_SIZE
    : NOW_PLAYING_COVER_SIZE_WEB
  const trackSources = coverSourcesForFile(file, size)
  const artist = String(artistName || '').trim()
  if (!artist) return trackSources

  const artistSources = coverSourcesForArtist(artist, [file], size)
  return Object.freeze(mergeCoverSources(trackSources, artistSources))
}

function clearCoverSourcesCache() {
  coverSourcesCache.clear()
}

async function invalidateArtistCoverArt(artistName = '') {
  const name = String(artistName || '').trim()
  if (!name) return
  clearCoverSourcesCache()
  await invalidateArtistCoverCaches(name)
  notifyLibraryChanged()
}

function warmLibraryCovers(items = []) {
  const native = isCapacitorNative()
  const entries = []
  const seenArtists = new Set()
  const artistLimit = native ? 80 : 24
  const fileSlice = native ? 40 : 48
  const batchLimit = native ? 80 : 96
  const concurrency = native ? 8 : 12

  for (const item of items) {
    const artist = String(item?.artist || '').trim()
    const file = String(item?.file || '').trim()
    if (!artist || !file || seenArtists.has(artist)) continue
    seenArtists.add(artist)
    entries.push(coverSourcesForArtist(artist, [file]))
    if (seenArtists.size >= artistLimit) break
  }

  for (const item of items.slice(0, fileSlice)) {
    const file = String(item?.file || '').trim()
    if (file) entries.push(coverSourcesForFile(file))
  }

  preloadCoverSourcesBatch(entries, { limit: batchLimit, concurrency })
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
  // Native clients fetch remote artwork through Capacitor's native HTTP bridge
  // (see imageLoader.resolveImageSrc), which reaches CDNs directly at the OS
  // layer. Routing those through the on-device embedded server's
  // /api/image-proxy made search/artist art depend on the embedded Python
  // process doing its own outbound fetches, which is unreliable on Android even
  // when the rest of the app has network. Only the web build proxies CDN images.
  if (isCapacitorNative()) return false
  return isCdnImageUrl(url)
}

// Search results upgrade every YouTube Music / Google thumbnail to 600x600 so
// the full-resolution image is available for album-art embedding on download.
// Rendering those full-size images in tiny list tiles is wasteful — and on the
// embedded Android APK each one is pulled through the Capacitor HTTP bridge as
// base64, so a page of 600x600 covers loads slowly. These CDNs accept a size
// suffix, so request a small thumbnail sized for the tile instead. The original
// (full-res) cover_url is untouched and still used for the actual download.
const GOOGLE_THUMB_HOST_SUFFIXES = ['googleusercontent.com', 'ggpht.com']

function cdnThumbnailUrl(url, size) {
  const value = String(url || '').trim()
  const px = Math.round(Number(size) || 0)
  if (!value || px <= 0) return value
  let host = ''
  try {
    host = new URL(value).hostname.toLowerCase()
  } catch {
    return value
  }
  const isGoogleThumb = GOOGLE_THUMB_HOST_SUFFIXES.some(
    (suffix) => host === suffix || host.endsWith(`.${suffix}`)
  )
  if (!isGoogleThumb) return value
  // Replace an existing "=w600-h600-..." sizing suffix, or append one.
  if (/=w\d+-h\d+/i.test(value)) {
    return value.replace(/=w\d+-h\d+[^/]*$/i, `=w${px}-h${px}-l90-rj`)
  }
  return `${value}=w${px}-h${px}-l90-rj`
}

// Display size for remote search-result thumbnails. Tiles render ~56-64px; 256
// keeps them crisp on high-DPI screens while staying far smaller than 600x600.
const SEARCH_THUMBNAIL_SIZE = 256

function searchCoverUrl(url, size = SEARCH_THUMBNAIL_SIZE) {
  return mediaUrl(cdnThumbnailUrl(url, size))
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

const LRC_TIMESTAMP_RE = /\[(\d{1,3}):(\d{2})(?:\.(\d{1,3}))?\]/g

function parseLrcText(text) {
  const lines = []
  for (const rawLine of String(text || '').split(/\r?\n/)) {
    const matches = [...rawLine.matchAll(LRC_TIMESTAMP_RE)]
    if (!matches.length) continue
    const lyric = rawLine.replace(LRC_TIMESTAMP_RE, '').trim()
    if (!lyric) continue
    for (const match of matches) {
      const minutes = Number.parseInt(match[1] || '0', 10)
      const seconds = Number.parseInt(match[2] || '0', 10)
      const fraction = match[3] ? Number.parseFloat(`0.${match[3]}`) : 0
      lines.push({
        time: Math.round((minutes * 60 + seconds + fraction) * 1000) / 1000,
        text: lyric,
      })
    }
  }
  lines.sort((a, b) => a.time - b.time)
  return lines
}

async function getLibraryLyricsSidecar(file) {
  const lrcFile = String(file || '').replace(/\.[^/.]+$/, '.lrc')
  if (!lrcFile || lrcFile === file) {
    return {
      data: { available: false, synced: false, lines: [], plain: '' },
    }
  }
  const res = await axios.get(apiAssetUrl(`/downloads/${encodePath(lrcFile)}`), {
    responseType: 'text',
    timeout: 10000,
  })
  const text = String(res.data || '')
  const lines = parseLrcText(text)
  return {
    data: {
      available: Boolean(lines.length || text.trim()),
      synced: Boolean(lines.length),
      lines,
      plain: lines.length ? '' : text.trim(),
    },
  }
}

function getLibraryLyrics(file) {
  return API.get('/api/library/lyrics', {
    params: { file },
    timeout: 10000,
    headers: { Accept: 'application/json' },
  }).then((res) => {
    if (typeof res.data === 'string') {
      return getLibraryLyricsSidecar(file)
    }
    return res
  }).catch(() => {
    return getLibraryLyricsSidecar(file)
  })
}

function checkLibraryOwned(items) {
  return API.post('/api/library/owned', { items })
}

function fetchAlbumTrackCounts(browseIds) {
  return API.post('/api/songs/album-track-counts', { browse_ids: browseIds })
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

function getHistory(limit = 500, reconcile = true) {
  return API.get('/api/history', { params: { limit, reconcile } })
}

function reconcileHistory(interruptMinutes = 15) {
  return API.post('/api/history/reconcile', null, {
    params: { interrupt_minutes: interruptMinutes },
  })
}

function retryHistoryItem(historyId) {
  return API.post(`/api/history/${historyId}/retry`)
}

function deleteHistoryItem(historyId) {
  return API.delete(`/api/history/${historyId}`)
}

function clearHistory() {
  return API.delete('/api/history')
}

function getCapabilities() {
  return API.get('/api/capabilities')
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
  coverUrlsForGenreFile,
  coverFallbackUrls,
  coverSourcesForFile,
  coverSourcesForGenreFile,
  coverSourcesForArtist,
  coverSourcesForNowPlaying,
  clearCoverSourcesCache,
  invalidateArtistCoverArt,
  warmLibraryCovers,
  refreshLibraryInBackground,
  libraryServerKey,
  apiAssetUrl,
  mediaUrl,
  searchCoverUrl,
  listDownloads,
  getLibraryFiles,
  getLibraryLyrics,
  checkLibraryOwned,
  fetchAlbumTrackCounts,
  getLibraryGenresStatus,
  deleteDownload,
  writePlaylistM3u,
  getQueue,
  removeQueueItem,
  clearQueue,
  getHistory,
  reconcileHistory,
  retryHistoryItem,
  deleteHistoryItem,
  clearHistory,
  getCapabilities,
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
