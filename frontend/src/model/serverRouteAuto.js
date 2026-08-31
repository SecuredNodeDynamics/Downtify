import { CapacitorHttp } from '@capacitor/core'

import {
  canonicalServerUrl,
  getActiveServerRoute,
  getStoredPrivateServerUrl,
  getStoredPublicServerUrl,
  isCapacitorNative,
  parseServerUrl,
  SERVER_ROUTE_PRIVATE,
  SERVER_ROUTE_PUBLIC,
  setActiveServerRoute,
  usesEmbeddedServer,
} from './serverConnection.js'

const PRIVATE_PROBE_MS = 2500

let autoSwitchStarted = false
let applyInFlight = null
let debounceTimer = null

export function choosePreferredServerRoute({
  privateUrl,
  publicUrl,
  privateReachable,
}) {
  const hasPrivate = Boolean(canonicalServerUrl(privateUrl))
  const hasPublic = Boolean(canonicalServerUrl(publicUrl))
  if (hasPrivate && hasPublic) {
    return privateReachable ? SERVER_ROUTE_PRIVATE : SERVER_ROUTE_PUBLIC
  }
  if (hasPrivate) return SERVER_ROUTE_PRIVATE
  if (hasPublic) return SERVER_ROUTE_PUBLIC
  return null
}

export function canAutoSelectServerRoute() {
  if (usesEmbeddedServer()) return false
  if (!isCapacitorNative()) return false
  return Boolean(
    canonicalServerUrl(getStoredPrivateServerUrl()) &&
      canonicalServerUrl(getStoredPublicServerUrl())
  )
}

function healthUrl(input) {
  const base = canonicalServerUrl(input)
  return base ? `${base}/api/health` : ''
}

function looksLikeHealthResponse(status, data) {
  if (!(status >= 200 && status < 300)) return false
  if (typeof data === 'string' && data.trim().startsWith('<')) return false
  if (data && typeof data === 'object' && typeof data.status === 'string') {
    return true
  }
  return true
}

export async function probeServerUrl(input, timeoutMs = PRIVATE_PROBE_MS) {
  const url = healthUrl(input)
  if (!url) return false
  try {
    if (isCapacitorNative() && typeof CapacitorHttp?.request === 'function') {
      const res = await CapacitorHttp.request({
        url,
        method: 'GET',
        connectTimeout: timeoutMs,
        readTimeout: timeoutMs,
      })
      return looksLikeHealthResponse(res.status, res.data)
    }
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), timeoutMs)
    try {
      const res = await fetch(url, {
        method: 'GET',
        signal: controller.signal,
        cache: 'no-store',
      })
      let data = null
      const type = res.headers.get('content-type') || ''
      if (type.includes('json')) {
        data = await res.json().catch(() => null)
      } else {
        data = await res.text().catch(() => '')
      }
      return looksLikeHealthResponse(res.status, data)
    } finally {
      clearTimeout(timer)
    }
  } catch {
    return false
  }
}

async function doApplyPreferredServerRoute() {
  if (!canAutoSelectServerRoute()) return false
  const privateUrl = getStoredPrivateServerUrl()
  const publicUrl = getStoredPublicServerUrl()
  const privateReachable = await probeServerUrl(privateUrl)
  const preferred = choosePreferredServerRoute({
    privateUrl,
    publicUrl,
    privateReachable,
  })
  if (!preferred) return false
  const current = getActiveServerRoute()
  const currentUrl = canonicalServerUrl(
    current === SERVER_ROUTE_PUBLIC ? publicUrl : privateUrl
  )
  const nextUrl = canonicalServerUrl(
    preferred === SERVER_ROUTE_PUBLIC ? publicUrl : privateUrl
  )
  if (current === preferred && currentUrl === nextUrl) return false
  setActiveServerRoute(preferred)
  return true
}

export async function applyPreferredServerRoute() {
  if (applyInFlight) return applyInFlight
  applyInFlight = doApplyPreferredServerRoute().finally(() => {
    applyInFlight = null
  })
  return applyInFlight
}

export function failOverToPublicServerRoute() {
  if (usesEmbeddedServer()) return false
  if (!canonicalServerUrl(getStoredPublicServerUrl())) return false
  if (getActiveServerRoute() === SERVER_ROUTE_PUBLIC) return false
  if (!canonicalServerUrl(getStoredPrivateServerUrl())) return false
  setActiveServerRoute(SERVER_ROUTE_PUBLIC)
  return true
}

export function startServerRouteAutoSwitch(onChanged) {
  if (autoSwitchStarted || typeof window === 'undefined') return
  autoSwitchStarted = true

  const run = () => {
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
      void applyPreferredServerRoute().then((changed) => {
        if (changed) onChanged?.()
      })
    }, 400)
  }

  window.addEventListener('online', run)
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') run()
  })

  if (isCapacitorNative()) {
    void import('@capacitor/app').then(({ App }) => {
      void App.addListener('appStateChange', ({ isActive }) => {
        if (isActive) run()
      })
    })
  }
}
