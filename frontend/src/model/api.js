// small file used as placeholder/settings for API calls via axios to server-side
import axios from 'axios' // used to connect to server backend in ./server folder
import config from '/src/config.js'

import { v4 as uuidv4 } from 'uuid'

console.log('using env:', process.env)
console.log('using config: ', config)

const API = axios.create({
  baseURL: `${config.PROTOCOL}//${config.BACKEND}:${config.PORT}${config.BASEURL}`,
})

const sessionID = uuidv4()
console.log('session ID: ', sessionID)

const SEMVER = /^\d+\.\d+\.\d+$/

function isValidVersion(value) {
  return typeof value === 'string' && SEMVER.test(value.trim())
}

function sanitizeStoredVersion() {
  const stored = localStorage.getItem('version')
  if (stored && !isValidVersion(stored)) {
    localStorage.removeItem('version')
  }
}

sanitizeStoredVersion()
getVersion()

const wsConnection = new WebSocket(
  `${config.WS_PROTOCOL}//${config.BACKEND}${
    config.PORT !== '' ? ':' + config.PORT : ''
  }${config.BASEURL}/api/ws?client_id=${sessionID}`
)

wsConnection.onopen = (event) => {
  console.log('websocket connection opened', event)
}

function getVersion() {
  API.get('/api/version')
    .then((res) => {
      const version = String(res.data ?? '').trim()
      if (!isValidVersion(version)) {
        console.warn(
          'Ignoring invalid /api/version response (is the backend running?)'
        )
        return
      }
      const prevItem = localStorage.getItem('version')
      console.log('Backend version: ', version)
      localStorage.setItem('version', version)
      if (prevItem != version) {
        location.reload()
      }
    })
    .catch((error) => {
      console.error(error)
      console.log('Error getting version, using 0')
      localStorage.setItem('version', '0.0.0')
    })
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

function check_for_update() {
  return API.get('/api/check_update')
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

function applyArtistImage(item) {
  return API.post('/api/metadata/artist-images/apply', {
    file: item.file,
    artist: item.artist,
    artist_id: item.artist_id,
  })
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
  return `/downloads/${encodePath(fileName)}`
}

function coverFileURL(fileName) {
  return `/cover?file=${encodeURIComponent(fileName)}`
}

function listDownloads() {
  return API.get('/list')
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

function getHistory() {
  return API.get('/api/history')
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
  return (wsConnection.onmessage = fn)
}
function ws_onerror(fn) {
  return (wsConnection.onerror = fn)
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
  listDownloads,
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
  getHealth,
  startMetadataScan,
  getMetadataScanStatus,
  applyMetadata,
  scanArtistImages,
  getArtistImageScanStatus,
  applyArtistImage,
  getRepairLog,
  ws_onmessage,
  ws_onerror,
  getVersion,
}
