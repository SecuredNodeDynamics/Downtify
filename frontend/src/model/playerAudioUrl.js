import { Capacitor } from '@capacitor/core'

import API from './api.js'
import { activeDownloadRoot } from './deviceStorage.js'
import { getServerMediaLocation } from './settings.js'
import { isCapacitorNative, usesEmbeddedServer } from './serverConnection.js'

const CAPACITOR_FILE_MARKER = '/_capacitor_file_'
const playbackUrlCache = new Map()
let playbackRootPromise = null

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

export function clearPlaybackUrlCache() {
  playbackUrlCache.clear()
  playbackRootPromise = null
}

async function playbackRootDir(mediaLocation = '') {
  if (!playbackRootPromise) {
    playbackRootPromise = activeDownloadRoot(mediaLocation)
  }
  return playbackRootPromise
}

/**
 * Resolve a library-relative audio path to a URL the HTML5 player can seek in.
 *
 * On the embedded Android APK, loopback HTTP streams often reject seeks even
 * when the server supports byte ranges. Reading the file directly through
 * Capacitor's file bridge gives the WebView a seekable local source.
 */
export async function resolvePlaybackUrl(file, options = {}) {
  const rel = String(file || '').trim()
  if (!rel) return ''

  const mediaLocation =
    options.mediaLocation !== undefined
      ? String(options.mediaLocation || '').trim()
      : getServerMediaLocation()
  const cacheKey = `${mediaLocation}\0${rel}`
  if (playbackUrlCache.has(cacheKey)) return playbackUrlCache.get(cacheKey)

  let url = ''
  if (usesEmbeddedServer() && isCapacitorNative()) {
    const root = await playbackRootDir(mediaLocation)
    if (root) {
      const absolute = `${root.replace(/\/+$/, '')}/${rel.replace(/^\/+/, '')}`
      url = Capacitor.convertFileSrc(absolute)
    }
  }
  if (!url) url = API.downloadFileURL(rel)

  playbackUrlCache.set(cacheKey, url)
  return url
}
