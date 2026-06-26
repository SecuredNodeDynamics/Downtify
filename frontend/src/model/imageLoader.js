import { Capacitor, CapacitorHttp } from '@capacitor/core'

import {
  deletePersistedImage,
  readPersistedImage,
  writePersistedImage,
} from './imageDiskCache.js'
import {
  buildApiBaseUrl,
  getServerConfig,
  isCapacitorNative,
} from './serverConnection.js'

const urlCache = new Map()
const sourceCache = new Map()
const preloadPromises = new Map()

function base64ToBlob(base64, mimeType) {
  const binary = atob(base64)
  const len = binary.length
  const bytes = new Uint8Array(len)
  for (let i = 0; i < len; i += 1) {
    bytes[i] = binary.charCodeAt(i)
  }
  return new Blob([bytes], { type: mimeType || 'image/jpeg' })
}

export function canLoadImageDirectly(url) {
  const value = String(url || '').trim()
  if (!value || value.startsWith('data:') || value.startsWith('blob:')) {
    return true
  }
  if (!isCapacitorNative()) return true
  try {
    const target = new URL(value)
    const server = new URL(buildApiBaseUrl(getServerConfig()))
    return target.origin === server.origin
  } catch {
    return false
  }
}

function persistImageInBackground(url) {
  void persistLoadedImage(url)
}

async function fetchDirectImageBlob(url) {
  try {
    const response = await fetch(url, { credentials: 'omit' })
    if (response.ok) return await response.blob()
  } catch {
    // Fall back to the native HTTP bridge below.
  }
  return fetchImageBlob(url)
}

export async function persistLoadedImage(url) {
  const value = String(url || '').trim()
  if (!value || !canLoadImageDirectly(value)) return ''

  const existing = await readPersistedImage(value)
  if (existing) {
    const blobUrl = URL.createObjectURL(existing)
    rememberResolvedUrl(value, blobUrl)
    return blobUrl
  }

  try {
    const blob = await fetchDirectImageBlob(value)
    await writePersistedImage(value, blob)
    const blobUrl = URL.createObjectURL(blob)
    rememberResolvedUrl(value, blobUrl)
    return blobUrl
  } catch {
    return ''
  }
}

function contentTypeFromHeaders(headers = {}) {
  const raw =
    headers['Content-Type'] ||
    headers['content-type'] ||
    headers['Content-type'] ||
    ''
  return String(raw).split(';')[0].trim() || 'image/jpeg'
}

async function fetchImageBlob(url) {
  const response = await CapacitorHttp.get({
    url,
    responseType: 'blob',
  })
  if (response.status < 200 || response.status >= 300) {
    throw new Error(`HTTP ${response.status}`)
  }
  const mime = contentTypeFromHeaders(response.headers)
  return base64ToBlob(response.data, mime)
}

async function fetchWithBrowser(url) {
  const response = await fetch(url, { credentials: 'omit' })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  const blob = await response.blob()
  return URL.createObjectURL(blob)
}

export function buildCoverSourceKey(src, fallbacks = []) {
  return [src, ...(fallbacks || [])]
    .map((url) => String(url || '').trim())
    .filter(Boolean)
    .join('\0')
}

export function getCachedCoverDisplay(sourceKey) {
  const key = String(sourceKey || '').trim()
  if (!key) return null
  return sourceCache.get(key) || null
}

export function rememberCoverDisplay(sourceKey, displaySrc, failed = false) {
  const key = String(sourceKey || '').trim()
  if (!key) return
  sourceCache.set(key, {
    displaySrc: String(displaySrc || ''),
    failed: Boolean(failed),
  })
}

export function invalidateFailedCoverDisplays() {
  for (const [key, value] of sourceCache.entries()) {
    if (value?.failed) sourceCache.delete(key)
  }
}

function urlMatchesArtistFolder(url, artistName) {
  const value = String(url || '').trim()
  const name = String(artistName || '').trim()
  if (!value || !name) return false
  if (!value.includes('artist-images/folder-preview')) return false
  try {
    const parsed = new URL(value, 'http://downtify.local')
    const folder = parsed.searchParams.get('folder') || ''
    return folder === name
  } catch {
    return value.includes(`folder=${encodeURIComponent(name)}`)
  }
}

/** Drop cached artist-folder cover URLs after a manual image repair/replace. */
export async function invalidateArtistCoverCaches(artistName = '') {
  const name = String(artistName || '').trim()
  if (!name) return

  for (const key of [...urlCache.keys()]) {
    if (urlMatchesArtistFolder(key, name)) {
      urlCache.delete(key)
      preloadPromises.delete(key)
      await deletePersistedImage(key)
    }
  }

  for (const [key, value] of sourceCache.entries()) {
    const display = String(value?.displaySrc || '')
    if (
      key.includes(name) ||
      urlMatchesArtistFolder(display, name) ||
      display.includes(name)
    ) {
      sourceCache.delete(key)
    }
  }
}

function onEmbeddedServerReady() {
  invalidateFailedCoverDisplays()
}

if (typeof window !== 'undefined') {
  window.addEventListener(
    'downtify-embedded-server-ready',
    onEmbeddedServerReady
  )
}

function rememberResolvedUrl(url, resolved) {
  const value = String(url || '').trim()
  const display = String(resolved || '').trim()
  if (!value || !display) return
  urlCache.set(value, display)
}

function preloadHttpImage(url) {
  const value = String(url || '').trim()
  if (!value) return Promise.resolve('')
  if (urlCache.has(value)) return Promise.resolve(urlCache.get(value))

  const pending = preloadPromises.get(value)
  if (pending) return pending

  const promise = new Promise((resolve, reject) => {
    const image = new Image()
    image.decoding = 'async'
    image.referrerPolicy = 'no-referrer'
    image.onload = () => {
      rememberResolvedUrl(value, value)
      persistImageInBackground(value)
      resolve(value)
    }
    image.onerror = () => reject(new Error(`Failed to preload image: ${value}`))
    image.src = value
  })
    .catch((error) => {
      preloadPromises.delete(value)
      throw error
    })
    .finally(() => {
      preloadPromises.delete(value)
    })

  preloadPromises.set(value, promise)
  return promise
}

export async function resolveImageSrc(url) {
  const value = String(url || '').trim()
  if (!value) return ''

  if (value.startsWith('data:') || value.startsWith('blob:')) {
    rememberResolvedUrl(value, value)
    return value
  }

  const cached = urlCache.get(value)
  if (cached) return cached

  if (!isCapacitorNative()) {
    // Serve a previously persisted copy first. The browser/WebView HTTP cache
    // is volatile and frequently evicted between sessions, which made covers
    // blank out and reload slowly after the app was closed and reopened. The
    // IndexedDB-backed disk cache survives restarts, so prefer it and fall back
    // to a normal network load (which repopulates the disk cache) on a miss.
    try {
      const persisted = await readPersistedImage(value)
      if (persisted) {
        const blobUrl = URL.createObjectURL(persisted)
        rememberResolvedUrl(value, blobUrl)
        return blobUrl
      }
    } catch (error) {
      console.warn('Failed to read persisted image:', value, error)
    }

    try {
      await preloadHttpImage(value)
      return urlCache.get(value) || value
    } catch (error) {
      console.warn('Failed to preload image:', value, error)
      return value
    }
  }

  if (canLoadImageDirectly(value)) {
    try {
      const persisted = await readPersistedImage(value)
      if (persisted) {
        const blobUrl = URL.createObjectURL(persisted)
        rememberResolvedUrl(value, blobUrl)
        return blobUrl
      }
      // Show the direct URL now, but cache the bytes in the background so the
      // next load is an instant blob from disk instead of re-hitting the
      // (slow, on embedded Android) server.
      rememberResolvedUrl(value, value)
      persistImageInBackground(value)
      return value
    } catch (error) {
      console.warn('Failed to load direct image on native:', value, error)
      return value
    }
  }

  try {
    if (Capacitor.isNativePlatform()) {
      const persisted = await readPersistedImage(value)
      if (persisted) {
        const blobUrl = URL.createObjectURL(persisted)
        rememberResolvedUrl(value, blobUrl)
        return blobUrl
      }

      const blob = await fetchImageBlob(value)
      void writePersistedImage(value, blob)
      const blobUrl = URL.createObjectURL(blob)
      rememberResolvedUrl(value, blobUrl)
      return blobUrl
    }

    const blobUrl = await fetchWithBrowser(value)
    rememberResolvedUrl(value, blobUrl)
    return blobUrl
  } catch (error) {
    console.warn('Failed to load image on native:', value, error)
    rememberResolvedUrl(value, value)
    return value
  }
}

export async function resolveNativeImageSrc(url) {
  return resolveImageSrc(url)
}

export async function preloadCoverSources({ src, fallbacks = [] } = {}) {
  const urls = [src, ...(fallbacks || [])]
    .map((url) => String(url || '').trim())
    .filter(Boolean)
  if (!urls.length) return ''

  const sourceKey = buildCoverSourceKey(src, fallbacks)
  const cached = getCachedCoverDisplay(sourceKey)
  if (cached?.displaySrc && !cached.failed) {
    return cached.displaySrc
  }

  for (const url of urls) {
    try {
      const resolved = await resolveImageSrc(url)
      if (resolved) {
        rememberCoverDisplay(sourceKey, resolved, false)
        if (canLoadImageDirectly(url) && !resolved.startsWith('blob:')) {
          void persistLoadedImage(url)
        }
        return resolved
      }
    } catch {
      // Try the next fallback candidate.
    }
  }

  return ''
}

export function preloadCoverSourcesBatch(
  entries = [],
  { limit = 24, concurrency = 6 } = {}
) {
  const queue = (entries || [])
    .map((entry) => ({
      src: entry?.src || '',
      fallbacks: entry?.fallbacks || [],
    }))
    .filter((entry) => entry.src || entry.fallbacks.length)
    .slice(0, Math.max(0, limit))

  if (!queue.length) return

  let cursor = 0
  const workerCount = Math.min(Math.max(1, concurrency), queue.length)
  const workers = Array.from({ length: workerCount }, async () => {
    while (cursor < queue.length) {
      const entry = queue[cursor]
      cursor += 1
      try {
        await preloadCoverSources(entry)
      } catch {
        // Ignore individual preload failures.
      }
    }
  })

  void Promise.all(workers)
}

export function clearNativeImageCache() {
  for (const blobUrl of urlCache.values()) {
    if (blobUrl.startsWith('blob:')) {
      URL.revokeObjectURL(blobUrl)
    }
  }
  urlCache.clear()
  sourceCache.clear()
  preloadPromises.clear()
  void import('./imageDiskCache.js').then(({ clearPersistedImageCache }) =>
    clearPersistedImageCache()
  )
}
