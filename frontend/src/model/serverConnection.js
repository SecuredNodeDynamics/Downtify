import { Capacitor } from '@capacitor/core'

const STORAGE_KEY = 'downtify-server-url'

// The embedded (on-device) backend listens here. Must match the port used by
// the native EmbeddedServer plugin / downtify.mobile.DEFAULT_PORT.
export const EMBEDDED_SERVER_PORT = 8765
export const EMBEDDED_SERVER_URL = `http://127.0.0.1:${EMBEDDED_SERVER_PORT}`

const CONNECTION_MODE_KEY = 'downtify-connection-mode'

export function isEmbeddedServerAvailable() {
  try {
    return (
      isCapacitorNative() &&
      Boolean(Capacitor?.isPluginAvailable?.('EmbeddedServer'))
    )
  } catch {
    return false
  }
}

// 'device' = run the on-device embedded backend; 'server' = use a remote
// Downtify server. The embedded APK defaults to 'device'; everything else is
// always 'server'.
export function getConnectionMode() {
  if (!isEmbeddedServerAvailable()) return 'server'
  try {
    const value = localStorage.getItem(CONNECTION_MODE_KEY)
    if (value === 'server' || value === 'device') return value
  } catch {
    // ignore storage errors
  }
  return 'device'
}

export function setConnectionMode(mode) {
  const normalized = mode === 'server' ? 'server' : 'device'
  try {
    localStorage.setItem(CONNECTION_MODE_KEY, normalized)
  } catch {
    // ignore storage errors
  }
}

export function usesEmbeddedServer() {
  return isEmbeddedServerAvailable() && getConnectionMode() === 'device'
}

const SPA_ROUTE_PREFIXES = [
  '/monitor',
  '/player',
  '/metadata',
  '/health',
  '/download',
  '/list',
  '/search',
  '/settings',
]

function deployBasePath() {
  return String(process.env.BASEURL || '').replace(/\/+$/, '')
}

function isSpaRoutePath(path) {
  const normalized = String(path || '').replace(/\/+$/, '') || ''
  if (!normalized) return false
  return SPA_ROUTE_PREFIXES.some(
    (prefix) => normalized === prefix || normalized.startsWith(`${prefix}/`)
  )
}

export function repairStoredServerUrl() {
  const stored = getStoredServerUrl()
  if (!stored) return
  const parsed = parseServerUrl(stored)
  if (!parsed || !isSpaRoutePath(parsed.BASEURL)) return
  const fixed = buildApiBaseUrl({ ...parsed, BASEURL: deployBasePath() })
  if (fixed !== stored.replace(/\/+$/, '')) {
    setStoredServerUrl(fixed)
  }
}

export function getStoredServerUrl() {
  try {
    return localStorage.getItem(STORAGE_KEY) || ''
  } catch {
    return ''
  }
}

export function setStoredServerUrl(url) {
  const trimmed = String(url || '').trim()
  try {
    if (trimmed) localStorage.setItem(STORAGE_KEY, trimmed)
    else localStorage.removeItem(STORAGE_KEY)
  } catch {
    // ignore quota / private mode errors
  }
}

export function usesCustomServerUrl() {
  return Boolean(getStoredServerUrl())
}

export function isCapacitorNative() {
  try {
    return Capacitor.isNativePlatform()
  } catch {
    return Boolean(
      typeof window !== 'undefined' && window.Capacitor?.isNativePlatform?.()
    )
  }
}

export function needsServerConnection() {
  if (usesEmbeddedServer()) return false
  return isCapacitorNative() && !usesCustomServerUrl()
}

export function parseServerUrl(input) {
  const raw = String(input || '')
    .trim()
    .replace(/\/+$/, '')
  if (!raw) return null
  try {
    const withScheme = /^[a-z][a-z0-9+.-]*:\/\//i.test(raw)
      ? raw
      : `http://${raw}`
    const url = new URL(withScheme)
    if (!url.hostname) return null
    let basePath = url.pathname || ''
    if (basePath.endsWith('/')) basePath = basePath.slice(0, -1)
    if (basePath === '/') basePath = ''
    return {
      PROTOCOL: url.protocol,
      WS_PROTOCOL: url.protocol === 'https:' ? 'wss:' : 'ws:',
      BACKEND: url.hostname,
      PORT: url.port,
      BASEURL: basePath,
    }
  } catch {
    return null
  }
}

function envOrLocation() {
  const hasWindow = typeof window !== 'undefined'
  return {
    PROTOCOL:
      process.env.PROTOCOL || (hasWindow ? window.location.protocol : 'http:'),
    WS_PROTOCOL:
      process.env.WS_PROTOCOL ||
      (hasWindow && window.location.protocol === 'https:' ? 'wss:' : 'ws:'),
    BACKEND:
      process.env.BACKEND ||
      (hasWindow ? window.location.hostname : 'localhost'),
    PORT:
      process.env.PORT !== undefined
        ? process.env.PORT
        : hasWindow
        ? window.location.port
        : '',
    BASEURL: process.env.BASEURL || '',
  }
}

export function getServerConfig() {
  if (usesEmbeddedServer()) {
    return parseServerUrl(EMBEDDED_SERVER_URL) || envOrLocation()
  }
  const stored = getStoredServerUrl()
  const parsed = stored ? parseServerUrl(stored) : null
  return parsed || envOrLocation()
}

export function buildApiBaseUrl(cfg = getServerConfig()) {
  const port = cfg.PORT ? `:${cfg.PORT}` : ''
  return `${cfg.PROTOCOL}//${cfg.BACKEND}${port}${cfg.BASEURL || ''}`
}

export function buildWsUrl(cfg, clientId) {
  const port = cfg.PORT ? `:${cfg.PORT}` : ''
  return `${cfg.WS_PROTOCOL}//${cfg.BACKEND}${port}${
    cfg.BASEURL || ''
  }/api/ws?client_id=${clientId}`
}

export function formatServerDisplay(cfg = getServerConfig()) {
  return buildApiBaseUrl(cfg)
}

export function getCurrentPageServerUrl() {
  if (typeof window === 'undefined') return ''
  if (isCapacitorNative()) return ''
  const { protocol, hostname, port } = window.location
  if (!hostname || protocol === 'file:' || protocol === 'capacitor:') {
    return ''
  }
  const origin = `${protocol}//${hostname}${port ? `:${port}` : ''}`
  const basePath = deployBasePath()
  return basePath ? `${origin}${basePath}` : origin
}

export function canConnectToCurrentPage() {
  return Boolean(getCurrentPageServerUrl())
}

export function isConnectedToCurrentPage() {
  if (isCapacitorNative()) return false
  const current = getCurrentPageServerUrl()
  if (!current) return !usesCustomServerUrl()
  const stored = getStoredServerUrl().trim()
  if (!stored) {
    const implicit = buildApiBaseUrl(envOrLocation())
    const page = buildApiBaseUrl(parseServerUrl(current))
    return implicit === page
  }
  const storedBase = buildApiBaseUrl(parseServerUrl(stored))
  const pageBase = buildApiBaseUrl(parseServerUrl(current))
  return storedBase === pageBase
}

export function configuredServerBaseUrl() {
  return buildApiBaseUrl(getServerConfig())
}

export function canSaveServerUrlInput(
  input,
  { native = isCapacitorNative() } = {}
) {
  const trimmed = String(input || '').trim()
  const parsed = parseServerUrl(trimmed)
  if (!parsed) return false
  if (native) return true
  return buildApiBaseUrl(parsed) !== configuredServerBaseUrl()
}

if (typeof window !== 'undefined') {
  repairStoredServerUrl()
}
