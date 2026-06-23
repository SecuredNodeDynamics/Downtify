import { Capacitor, CapacitorHttp } from '@capacitor/core'

import { isCapacitorNative } from './serverConnection.js'

const blobCache = new Map()

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

export async function resolveNativeImageSrc(url) {
  const value = String(url || '').trim()
  if (!value || !isCapacitorNative()) {
    return value
  }

  const cached = blobCache.get(value)
  if (cached) return cached

  try {
    const blobUrl = Capacitor.isNativePlatform()
      ? await fetchWithCapacitorHttp(value)
      : await fetchWithBrowser(value)
    blobCache.set(value, blobUrl)
    return blobUrl
  } catch (error) {
    console.warn('Failed to load image on native:', value, error)
    return value
  }
}

export function clearNativeImageCache() {
  for (const blobUrl of blobCache.values()) {
    if (blobUrl.startsWith('blob:')) {
      URL.revokeObjectURL(blobUrl)
    }
  }
  blobCache.clear()
}
