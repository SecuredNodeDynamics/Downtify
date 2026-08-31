import { Capacitor } from '@capacitor/core'

const STORAGE_KEY = 'downtify-server-url'
const PRIVATE_URL_KEY = 'downtify-server-url-private'
const PUBLIC_URL_KEY = 'downtify-server-url-public'
const ACTIVE_ROUTE_KEY = 'downtify-server-url-active'

export const SERVER_ROUTE_PRIVATE = 'private'
export const SERVER_ROUTE_PUBLIC = 'public'

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

// 'device' = on-phone engine at 127.0.0.1:8765 (not Docker / Cloudflare).
// 'server' = saved LAN IP or public tunnel URL.
export function getConnectionMode() {
  if (!isEmbeddedServerAvailable()) return 'server'
  try {
    const value = localStorage.getItem(CONNECTION_MODE_KEY)
    if (value === 'server' || value === 'device') return value
  } catch {
    // ignore storage errors
  }
  // A saved LAN IP or Cloudflare URL means this install talks to a real
  // Downtify server. Do not default to the on-device 127.0.0.1 engine.
  if (getStoredServerUrl()) return 'server'
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

function readStorage(key) {
  try {
    return localStorage.getItem(key) || ''
  } catch {
    return ''
  }
}

function writeStorage(key, value) {
  const trimmed = String(value || '').trim()
  try {
    if (trimmed) localStorage.setItem(key, trimmed)
    else localStorage.removeItem(key)
  } catch {
    // ignore quota / private mode errors
  }
}

const IPV4_HOST = /^(?:\d{1,3}\.){3}\d{1,3}$/

export function classifyServerUrl(input) {
  const parsed = parseServerUrl(input)
  if (!parsed) return null
  const host = String(parsed.BACKEND || '')
    .trim()
    .toLowerCase()
    .replace(/^\[|\]$/g, '')
  if (
    host === 'localhost' ||
    host === '127.0.0.1' ||
    host === '::1' ||
    host.endsWith('.local') ||
    host.endsWith('.lan') ||
    host.endsWith('.home') ||
    host.endsWith('.internal')
  ) {
    return SERVER_ROUTE_PRIVATE
  }
  if (IPV4_HOST.test(host) || host.includes(':')) {
    return SERVER_ROUTE_PRIVATE
  }
  return SERVER_ROUTE_PUBLIC
}

export function getStoredPrivateServerUrl() {
  migrateServerAddressSlots()
  return readStorage(PRIVATE_URL_KEY)
}

export function getStoredPublicServerUrl() {
  migrateServerAddressSlots()
  return readStorage(PUBLIC_URL_KEY)
}

export function getActiveServerRoute() {
  migrateServerAddressSlots()
  const stored = readStorage(ACTIVE_ROUTE_KEY)
  if (stored === SERVER_ROUTE_PUBLIC || stored === SERVER_ROUTE_PRIVATE) {
    return stored
  }
  const active = readStorage(STORAGE_KEY)
  const classified = classifyServerUrl(active)
  if (classified) return classified
  if (readStorage(PRIVATE_URL_KEY)) return SERVER_ROUTE_PRIVATE
  if (readStorage(PUBLIC_URL_KEY)) return SERVER_ROUTE_PUBLIC
  return SERVER_ROUTE_PRIVATE
}

export function setActiveServerRoute(route) {
  const normalized =
    route === SERVER_ROUTE_PUBLIC ? SERVER_ROUTE_PUBLIC : SERVER_ROUTE_PRIVATE
  writeStorage(ACTIVE_ROUTE_KEY, normalized)
  const url =
    normalized === SERVER_ROUTE_PUBLIC
      ? readStorage(PUBLIC_URL_KEY)
      : readStorage(PRIVATE_URL_KEY)
  writeStorage(STORAGE_KEY, url)
}

export function setStoredPrivateServerUrl(url) {
  writeStorage(PRIVATE_URL_KEY, url)
  if (getActiveServerRoute() === SERVER_ROUTE_PRIVATE) {
    writeStorage(STORAGE_KEY, url)
  }
}

export function setStoredPublicServerUrl(url) {
  writeStorage(PUBLIC_URL_KEY, url)
  if (getActiveServerRoute() === SERVER_ROUTE_PUBLIC) {
    writeStorage(STORAGE_KEY, url)
  }
}

export function migrateServerAddressSlots() {
  const active = readStorage(STORAGE_KEY)
  const priv = readStorage(PRIVATE_URL_KEY)
  const pub = readStorage(PUBLIC_URL_KEY)
  if (priv || pub) {
    if (!readStorage(ACTIVE_ROUTE_KEY)) {
      const kind =
        classifyServerUrl(active) ||
        (priv ? SERVER_ROUTE_PRIVATE : SERVER_ROUTE_PUBLIC)
      writeStorage(ACTIVE_ROUTE_KEY, kind)
    }
    if (!active) {
      const route = readStorage(ACTIVE_ROUTE_KEY)
      const url = route === SERVER_ROUTE_PUBLIC ? pub : priv || pub
      if (url) writeStorage(STORAGE_KEY, url)
    }
    return
  }
  if (!active) return
  const kind = classifyServerUrl(active) || SERVER_ROUTE_PRIVATE
  if (kind === SERVER_ROUTE_PUBLIC) writeStorage(PUBLIC_URL_KEY, active)
  else writeStorage(PRIVATE_URL_KEY, active)
  writeStorage(ACTIVE_ROUTE_KEY, kind)
}

export function getStoredServerUrl() {
  migrateServerAddressSlots()
  return readStorage(STORAGE_KEY)
}

export function setStoredServerUrl(url) {
  const trimmed = String(url || '').trim()
  writeStorage(STORAGE_KEY, trimmed)
  if (!trimmed) return
  const kind = classifyServerUrl(trimmed) || SERVER_ROUTE_PRIVATE
  if (kind === SERVER_ROUTE_PUBLIC) writeStorage(PUBLIC_URL_KEY, trimmed)
  else writeStorage(PRIVATE_URL_KEY, trimmed)
  writeStorage(ACTIVE_ROUTE_KEY, kind)
}

export function clearActiveServerUrl() {
  writeStorage(STORAGE_KEY, '')
}

export function clearSavedServerAddresses() {
  writeStorage(STORAGE_KEY, '')
  writeStorage(PRIVATE_URL_KEY, '')
  writeStorage(PUBLIC_URL_KEY, '')
  writeStorage(ACTIVE_ROUTE_KEY, '')
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

export function buildWsUrl(cfg, clientId, token = '') {
  const port = cfg.PORT ? `:${cfg.PORT}` : ''
  const params = new URLSearchParams({ client_id: String(clientId || '') })
  if (token) params.set('token', token)
  return `${cfg.WS_PROTOCOL}//${cfg.BACKEND}${port}${
    cfg.BASEURL || ''
  }/api/ws?${params}`
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
  migrateServerAddressSlots()
}
