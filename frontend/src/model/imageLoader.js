import { Capacitor, CapacitorHttp } from '@capacitor/core'

import { isCapacitorNative } from './serverConnection.js'

const urlCache = new Map()
const sourceCache = new Map()
const preloadPromises = new Map()

function base64ToBlob(base64, mimeType) {
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i)
  }
  return new Blob([bytes], { type: mimeType || 'image/jpeg' })
}

function contentTypeFromHeaders(headers = {}) {
  const raw =
    headers['Content-Type'] ||
    headers['content-type'] ||
    headers['Content-type'] ||
    ''
  return String(raw).split(';')[0].trim() || 'image/jpeg'
}

async function fetchWithCapacitorHttp(url) {
  const response = await CapacitorHttp.get({
    url,
    responseType: 'blob',
  })
  if (response.status < 200 || response.status >= 300) {
    throw new Error(`HTTP ${response.status}`)
  }
  const mime = contentTypeFromHeaders(response.headers)
  const blob = base64ToBlob(response.data, mime)
  return URL.createObjectURL(blob)
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
    try {
      await preloadHttpImage(value)
      return urlCache.get(value) || value
    } catch (error) {
      console.warn('Failed to preload image:', value, error)
      return value
    }
  }

  try {
    const blobUrl = Capacitor.isNativePlatform()
      ? await fetchWithCapacitorHttp(value)
      : await fetchWithBrowser(value)
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
        return resolved
      }
    } catch {
      // Try the next fallback candidate.
    }
  }

  return ''
}

export function preloadCoverSourcesBatch(entries = [], { limit = 24 } = {}) {
  const queue = (entries || [])
    .map((entry) => ({
      src: entry?.src || '',
      fallbacks: entry?.fallbacks || [],
    }))
    .filter((entry) => entry.src || entry.fallbacks.length)
    .slice(0, Math.max(0, limit))

  void Promise.allSettled(queue.map((entry) => preloadCoverSources(entry)))
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
}
