import { ref, computed } from 'vue'

import API from '/src/model/api'
import { useDownloadDestination } from '/src/model/downloadDestination'
import { useSettingsManager } from '/src/model/settings'
import { needsServerConnection } from '/src/model/serverConnection'
import { notifyLibraryChanged } from '/src/model/librarySession'
import {
  notifyDownloadHistory,
  upsertHistoryItem,
} from '/src/model/downloadHistory'
import { isMediaOwned } from '/src/model/libraryOwnership'
import {
  supportsDeviceStorage,
  activeDownloadRoot,
  scanDownloadedFile,
} from '/src/model/deviceStorage'

const downloadDestination = useDownloadDestination()
const moduleSettings = useSettingsManager()

const STATUS = {
  QUEUED: 'In Queue',
  DOWNLOADING: 'Downloading...',
  DOWNLOADED: 'Done',
  ERROR: 'Error',
}

const downloadQueue = ref([])
const activeQueue = computed(() =>
  [...downloadQueue.value].sort((a, b) => (b.queuedAt || 0) - (a.queuedAt || 0))
)
const activeDownloadCount = computed(() => activeQueue.value.length)

class DownloadItem {
  constructor(song) {
    this.song = song
    this.web_status = STATUS.QUEUED
    this.progress = 0
    this.message = ''
    this.web_download_url = null
    this.filename = null
    this.queuedAt = Date.now()
  }
  setDownloading() {
    this.web_status = STATUS.DOWNLOADING
  }
  setDownloaded() {
    this.web_status = STATUS.DOWNLOADED
  }
  setError() {
    this.web_status = STATUS.ERROR
  }
  setWebURL(URL) {
    this.web_download_url = URL
  }
  setFilename(name) {
    this.filename = name
  }
  isQueued() {
    return this.song.song_id !== undefined ? true : false
    // return this.web_status === STATUS.QUEUED
  }
  isDownloading() {
    return this.web_status === STATUS.DOWNLOADING
  }
  isDownloaded() {
    return this.web_status === STATUS.DOWNLOADED
  }
  isErrored() {
    return this.web_status === STATUS.ERROR
  }
  wsUpdate(message) {
    this.progress = message.progress
    this.message = message.message
  }
}

export function useProgressTracker() {
  function songKey(song) {
    return String(song?.song_id || song?.url || '')
  }

  function _findIndex(song) {
    const key = songKey(song)
    if (!key) return -1
    return downloadQueue.value.findIndex(
      (downloadItem) => songKey(downloadItem.song) === key
    )
  }
  function appendSong(song) {
    const downloadItem = new DownloadItem(song)
    downloadQueue.value.unshift(downloadItem)
  }
  function removeSong(song) {
    const key = songKey(song)
    downloadQueue.value = downloadQueue.value.filter(
      (downloadItem) => songKey(downloadItem.song) !== key
    )
  }

  function removeFromQueue(song) {
    removeSong(song)
    const songId = songKey(song)
    if (songId) {
      API.removeQueueItem(songId).catch(() => {})
    }
  }

  function getBySong(song) {
    const idx = _findIndex(song)
    if (idx === -1) return null
    return downloadQueue.value[_findIndex(song)]
  }

  return {
    appendSong,
    removeSong,
    removeFromQueue,
    getBySong,
    downloadQueue,
    activeQueue,
    activeDownloadCount,
  }
}

const progressTracker = useProgressTracker()

function completeQueueItem(song, item) {
  if (item) {
    maybeSaveToLocalMachine(item)
    maybeScanDeviceLibrary(item)
  }
  progressTracker.removeFromQueue(song)
  notifyLibraryChanged()
}

function maybeScanDeviceLibrary(item) {
  if (!item?.filename) return
  scanDeviceLibraryPath(item.filename)
}

/**
 * Ask Android's MediaScanner to (re)index a library-relative path. Used both
 * after a download (to add the file) and after a delete (scanning a path whose
 * file is gone removes its stale MediaStore entry, so the track actually
 * disappears from the device's music apps).
 */
export function scanDeviceLibraryPath(relativeFile) {
  if (!relativeFile || !supportsDeviceStorage()) return
  const settingsLocation =
    moduleSettings.settings.value.server_media_location || ''
  activeDownloadRoot(settingsLocation)
    .then((root) => {
      if (!root) return
      const rel = String(relativeFile).replace(/^\/+/, '')
      scanDownloadedFile(`${root.replace(/\/+$/, '')}/${rel}`)
    })
    .catch(() => {
      // Scanning is best-effort.
    })
}

function maybeSaveToLocalMachine(item) {
  if (
    !item?.web_download_url ||
    downloadDestination.destination.value !== 'local'
  ) {
    return
  }
  downloadDestination
    .saveToLocalMachine(item.web_download_url, item.filename)
    .catch((err) => {
      console.warn('Local save failed:', err.message)
    })
}

API.ws_onmessage((event) => {
  try {
    const data = JSON.parse(event.data)
    if (data?.event === 'history_changed') {
      if (data.history_item) upsertHistoryItem(data.history_item)
      notifyDownloadHistory({ immediate: true })
      return
    }

    if (data.history_item) {
      upsertHistoryItem(data.history_item)
    }

    const status = data?.status
    if (status === 'done' || status === 'error') {
      notifyDownloadHistory({ immediate: true })
    } else if (status === 'queued') {
      notifyDownloadHistory()
    }

    if (!data?.song) return
    let item = progressTracker.getBySong(data.song)
    if (!item) {
      progressTracker.appendSong(data.song)
      item = progressTracker.getBySong(data.song)
      if (!item) return
    }
    if (data.status === 'done') {
      item.progress = 100
      item.message = data.message || ''
      if (data.filename) {
        item.setWebURL(API.downloadFileURL(data.filename))
        item.setFilename(data.filename)
      }
      completeQueueItem(data.song, item)
    } else if (data.status === 'error') {
      item.wsUpdate(data)
      completeQueueItem(data.song, item)
    } else if (data.status === 'queued') {
      item.message = data.message || ''
    } else {
      item.wsUpdate(data)
      if (!item.isDownloading()) item.setDownloading()
    }
  } catch (error) {
    console.warn('Ignoring invalid WebSocket message:', error)
  }
})
API.ws_onerror((event) => {
  console.log('websocket error:', event)
})

async function _hydrateFromServer() {
  if (needsServerConnection()) return
  downloadQueue.value = downloadQueue.value.filter(
    (item) => !item.isDownloaded() && !item.isErrored()
  )
  try {
    const res = await API.getQueue()
    const jobs = res.data || []
    for (const job of jobs) {
      if (job.status === 'done' || job.status === 'error') continue
      const key = String(job.song?.song_id || job.song?.url || '')
      if (
        key &&
        downloadQueue.value.some(
          (i) => String(i.song?.song_id || i.song?.url || '') === key
        )
      ) {
        continue
      }
      const item = new DownloadItem(job.song)
      if (job.status === 'downloading') {
        item.setDownloading()
        item.progress = job.progress || 0
        item.message = job.message || ''
      } else {
        item.message = job.message || ''
      }
      downloadQueue.value.unshift(item)
    }
  } catch (e) {
    console.log('Failed to load queue from server:', e)
  }
}

_hydrateFromServer()

export function useDownloadManager() {
  const loading = ref(false)
  const settingsManager = useSettingsManager()

  function queueBatch(songs, playlistUrl = '') {
    const generateM3u = settingsManager.settings.value.generate_m3u !== false
    for (const song of songs) {
      if (!progressTracker.getBySong(song)) {
        progressTracker.appendSong(song)
      }
    }
    return API.downloadBatch({
      songs,
      playlist_url: playlistUrl,
      generate_m3u: generateM3u,
    })
      .then((res) => {
        notifyDownloadHistory({ immediate: true })
        return res
      })
      .catch((err) => {
        console.log('Batch submit failed:', err.message)
        return { failed: true, error: err.message }
      })
  }

  function fromURL(url) {
    const isPlaylistURL = (url || '').includes('://open.spotify.com/playlist/')
    loading.value = true
    return API.open(url)
      .then((res) => {
        console.log('Received Response:', res)
        if (res.status !== 200) {
          console.log('Error:', res)
          return
        }
        const songs = res.data
        if (Array.isArray(songs)) {
          return queueBatch(songs, isPlaylistURL ? url : '')
        } else {
          console.log('Opened Song:', songs)
          queue(songs)
        }
      })
      .catch((err) => {
        console.log('Other Error:', err.message)
      })
      .finally(() => {
        loading.value = false
      })
  }

  async function queueAlbum(album) {
    if (!album.browse_id) {
      return { album, failed: true, error: 'Missing album browse id' }
    }
    if (await isMediaOwned(album)) return { album, skipped: true }

    loading.value = true
    try {
      const res = await API.openYoutubeAlbum(album.browse_id)
      const songs = Array.isArray(res.data) ? res.data : []
      if (res.status !== 200 || !songs.length) {
        return { album, failed: true, error: 'No tracks found for this album' }
      }
      const queued = await queueBatch(songs)
      if (queued?.failed) {
        return { album, failed: true, error: queued.error }
      }
      return { album, queued: true, count: songs.length }
    } catch (err) {
      console.log('Album queue failed:', err.message)
      return { album, failed: true, error: err.message }
    } finally {
      loading.value = false
    }
  }

  function download(song) {
    console.log('Downloading', song)
    progressTracker.getBySong(song).setDownloading()
    return API.download(song)
      .then((res) => {
        console.log('Received Response:', res)
        if (res.status === 200) {
          let filename = res.data
          console.log('Download Complete:', filename)
          const item = progressTracker.getBySong(song)
          if (item) {
            item.setWebURL(API.downloadFileURL(filename))
            item.setFilename(filename)
          }
          completeQueueItem(song, item)
          notifyDownloadHistory({ immediate: true })
          return { song, filename }
        } else {
          console.log('Error:', res)
          completeQueueItem(song, progressTracker.getBySong(song))
          return { song, filename: null }
        }
      })
      .catch((err) => {
        console.log('Other Error:', err.message)
        completeQueueItem(song, progressTracker.getBySong(song))
        return { song, filename: null }
      })
  }

  async function queue(song, beginDownload = true) {
    if (!song) return Promise.resolve({ song, filename: null })
    if (await isMediaOwned(song)) {
      return Promise.resolve({ song, filename: null, skipped: true })
    }
    if (song.media_type === 'album') return queueAlbum(song)
    progressTracker.appendSong(song)
    if (beginDownload) return download(song)
    return Promise.resolve({ song, filename: null })
  }

  function retryWithAudio(song, youtubeVideoId) {
    const overriddenSong = { ...song, youtube_id: youtubeVideoId }
    const item = progressTracker.getBySong(song)
    if (item) {
      item.song.youtube_id = youtubeVideoId
      item.setDownloading()
      item.progress = 0
      item.message = ''
    }
    return API.download(overriddenSong)
      .then((res) => {
        const it = progressTracker.getBySong(overriddenSong)
        if (res.status === 200) {
          const filename = res.data
          if (it) {
            it.setWebURL(API.downloadFileURL(filename))
            it.setFilename(filename)
          }
          completeQueueItem(overriddenSong, it)
          notifyDownloadHistory({ immediate: true })
          return { song: overriddenSong, filename }
        }
        completeQueueItem(overriddenSong, it)
        notifyDownloadHistory({ immediate: true })
        return { song: overriddenSong, filename: null }
      })
      .catch((err) => {
        console.error('retryWithAudio error:', err.message)
        completeQueueItem(
          overriddenSong,
          progressTracker.getBySong(overriddenSong)
        )
        return { song: overriddenSong, filename: null }
      })
  }

  function remove(song) {
    progressTracker.removeFromQueue(song)
  }

  async function clearAll() {
    await API.clearQueue()
    downloadQueue.value = []
  }

  return {
    fromURL,
    download,
    queue,
    queueBatch,
    retryWithAudio,
    remove,
    clearAll,
    loading,
  }
}
