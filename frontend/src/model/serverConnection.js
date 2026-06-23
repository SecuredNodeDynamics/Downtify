const STORAGE_KEY = 'downtify-server-url'

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
      process.env.PROTOCOL ||
      (hasWindow ? window.location.protocol : 'http:'),
    WS_PROTOCOL:
      process.env.WS_PROTOCOL ||
      (hasWindow && window.location.protocol === 'https:' ? 'wss:' : 'ws:'),
    BACKEND:
      process.env.BACKEND || (hasWindow ? window.location.hostname : 'localhost'),
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
  return `${cfg.WS_PROTOCOL}//${cfg.BACKEND}${port}${cfg.BASEURL || ''}/api/ws?client_id=${clientId}`
}

export function formatServerDisplay(cfg = getServerConfig()) {
  return buildApiBaseUrl(cfg)
}
