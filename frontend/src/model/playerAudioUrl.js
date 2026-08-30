import { Capacitor } from '@capacitor/core'

import API from './api.js'
import { activeDownloadRoot } from './deviceStorage.js'
import { getServerMediaLocation } from './settings.js'
import { isCapacitorNative, usesEmbeddedServer } from './serverConnection.js'

const CAPACITOR_FILE_MARKER = '/_capacitor_file_'
const playbackUrlCache = new Map()
const playbackFallbackCache = new Map()
const playbackRootPromises = new Map()

export function normalizeAudioUrl(url) {
  const value = String(url || '').trim()
  if (!value) return ''
  try {
    const resolved = value.includes('://')
      ? new URL(value)
      : new URL(
          value,
          typeof window !== 'undefined' && window.location?.origin
            ? window.location.origin
            : 'http://local.invalid'
        )
    let path = `${resolved.pathname}${resolved.search}`
    const markerIndex = path.indexOf(CAPACITOR_FILE_MARKER)
    if (markerIndex >= 0) {
      path = decodeURIComponent(
        path.slice(markerIndex + CAPACITOR_FILE_MARKER.length)
      )
    }
    return path
  } catch {
    return value
  }
}

export function isSameAudioUrl(currentUrl, nextUrl) {
  if (!currentUrl || !nextUrl) return false
  return normalizeAudioUrl(currentUrl) === normalizeAudioUrl(nextUrl)
}

export function isSameAudioFile(currentUrl, file) {
  const rel = String(file || '').trim()
  if (!currentUrl || !rel) return false
  const normalized = normalizeAudioUrl(currentUrl)
  if (normalized === rel || normalized.endsWith(`/${rel}`)) return true
  const downloadPath = `/downloads/${rel
    .split('/')
    .map(encodeURIComponent)
    .join('/')}`
  return normalized === downloadPath || normalized.endsWith(downloadPath)
}

export function isCapacitorFilePlaybackUrl(url) {
  return String(url || '').includes(CAPACITOR_FILE_MARKER)
}

/**
 * True when a path is a real on-device Android folder the WebView/FileProvider
 * can read. Docker/NAS leftovers like ``/downloads`` must not be used for
 * Capacitor.convertFileSrc — the library API still lists files from DOWNLOAD_DIR.
 */
export function isUsableEmbeddedMediaRoot(path) {
  const value = String(path || '')
    .trim()
    .replace(/\\/g, '/')
  if (!value) return false
  if (
    value === '/downloads' ||
    value.startsWith('/downloads/') ||
    value === '/data' ||
    value.startsWith('/mnt/') ||
    value.startsWith('/opt/') ||
    value.startsWith('/var/')
  ) {
    return false
  }
  return (
    value.startsWith('/storage/') ||
    value.startsWith('/sdcard') ||
    value.startsWith('/data/user/') ||
    value.startsWith('/data/data/') ||
    value.includes('/Android/data/') ||
    value.includes('/emulated/')
  )
}

export function embeddedMediaLocationHint(mediaLocation = '') {
  const hinted = String(mediaLocation || '').trim()
  if (isUsableEmbeddedMediaRoot(hinted)) return hinted
  return ''
}

export function clearPlaybackUrlCache() {
  playbackUrlCache.clear()
  playbackFallbackCache.clear()
  playbackRootPromises.clear()
}

async function playbackRootDir(mediaLocation = '') {
  const usableHint = embeddedMediaLocationHint(mediaLocation)
  const cacheKey = usableHint || '__embedded_default__'
  if (!playbackRootPromises.has(cacheKey)) {
    playbackRootPromises.set(
      cacheKey,
      activeDownloadRoot(usableHint).then((root) => {
        const resolved = String(root || '').trim()
        return isUsableEmbeddedMediaRoot(resolved) ? resolved : ''
      })
    )
  }
  return playbackRootPromises.get(cacheKey)
}

function httpPlaybackUrl(file) {
  return API.downloadFileURL(file)
}

export function playbackHttpFallbackUrl(file, options = {}) {
  const rel = String(file || '').trim()
  if (!rel) return ''
  const mediaLocation =
    options.mediaLocation !== undefined
      ? String(options.mediaLocation || '').trim()
      : getServerMediaLocation()
  const cacheKey = `${embeddedMediaLocationHint(mediaLocation)}\0${rel}`
  if (playbackFallbackCache.has(cacheKey)) {
    return playbackFallbackCache.get(cacheKey)
  }
  return httpPlaybackUrl(rel)
}

/**
 * Resolve a library-relative audio path to a URL the HTML5 player can seek in.
 *
 * Prefer the Capacitor file bridge when the library root is a real Android
 * path (seeks are more reliable than loopback HTTP). Always remember the
 * ``/downloads/...`` URL so playback can fall back if the file bridge 404s.
 */
export async function resolvePlaybackUrl(file, options = {}) {
  const rel = String(file || '').trim()
  if (!rel) return ''

  const mediaLocation =
    options.mediaLocation !== undefined
      ? String(options.mediaLocation || '').trim()
      : getServerMediaLocation()
  const cacheKey = `${embeddedMediaLocationHint(mediaLocation)}\0${rel}`
  if (playbackUrlCache.has(cacheKey)) return playbackUrlCache.get(cacheKey)

  const httpUrl = httpPlaybackUrl(rel)
  let url = httpUrl
  if (usesEmbeddedServer() && isCapacitorNative()) {
    const root = await playbackRootDir(mediaLocation)
    if (root) {
      const absolute = `${root.replace(/\/+$/, '')}/${rel.replace(/^\/+/, '')}`
      url = Capacitor.convertFileSrc(absolute)
    }
  }

  playbackUrlCache.set(cacheKey, url)
  playbackFallbackCache.set(
    cacheKey,
    url && url !== httpUrl ? httpUrl : ''
  )
  return url
}
