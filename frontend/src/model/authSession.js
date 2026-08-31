import { computed, ref } from 'vue'

import {
  buildApiBaseUrl,
  getServerConfig,
  getStoredPrivateServerUrl,
  getStoredPublicServerUrl,
  parseServerUrl,
} from './serverConnection.js'

const TOKEN_PREFIX = 'downtify-session-token:'

export const AUTH_CHANGED_EVENT = 'downtify:auth-changed'

const status = ref({
  auth_required: false,
  setup_required: false,
  authenticated: false,
  user: null,
  profiles: [],
})
const loading = ref(false)
const errorMessage = ref('')
const ready = ref(false)

export function sessionStorageKey(
  baseUrl = buildApiBaseUrl(getServerConfig())
) {
  return `${TOKEN_PREFIX}${String(baseUrl || '').replace(/\/+$/, '')}`
}

function canonicalBase(url) {
  const parsed = parseServerUrl(url)
  return parsed ? buildApiBaseUrl(parsed).replace(/\/+$/, '') : ''
}

function siblingRemoteBaseUrls(baseUrl) {
  const priv = canonicalBase(getStoredPrivateServerUrl())
  const pub = canonicalBase(getStoredPublicServerUrl())
  if (!priv || !pub) return []
  const current = canonicalBase(baseUrl || buildApiBaseUrl(getServerConfig()))
  if (current === priv) return [pub]
  if (current === pub) return [priv]
  return []
}

export function getStoredAuthToken(baseUrl) {
  if (typeof localStorage === 'undefined') return ''
  try {
    const primary = localStorage.getItem(sessionStorageKey(baseUrl)) || ''
    if (primary) return primary
    for (const sibling of siblingRemoteBaseUrls(baseUrl)) {
      const token = localStorage.getItem(sessionStorageKey(sibling)) || ''
      if (token) return token
    }
    return ''
  } catch {
    return ''
  }
}

export function storeAuthToken(token, baseUrl) {
  if (typeof localStorage === 'undefined') return
  const key = sessionStorageKey(baseUrl)
  try {
    if (token) localStorage.setItem(key, token)
    else localStorage.removeItem(key)
    for (const sibling of siblingRemoteBaseUrls(baseUrl)) {
      const siblingKey = sessionStorageKey(sibling)
      if (token) localStorage.setItem(siblingKey, token)
      else localStorage.removeItem(siblingKey)
    }
  } catch {
    // ignore quota / private mode
  }
}

export function clearAuthToken(baseUrl) {
  storeAuthToken('', baseUrl)
}

export function applyAuthStatus(data) {
  const next = {
    auth_required: Boolean(data?.auth_required),
    setup_required: Boolean(data?.setup_required),
    authenticated: Boolean(data?.authenticated && data?.user),
    user: data?.user || null,
    profiles: Array.isArray(data?.profiles) ? data.profiles : [],
  }
  status.value = next
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent(AUTH_CHANGED_EVENT, { detail: next }))
  }
  return next
}

function headerAuthorization(headers) {
  if (!headers) return ''
  if (typeof headers.get === 'function') {
    return String(
      headers.get('Authorization') || headers.get('authorization') || ''
    )
  }
  const json = typeof headers.toJSON === 'function' ? headers.toJSON() : headers
  return String(json?.Authorization || json?.authorization || '')
}

export function requestHasAuthorization(config) {
  const headers = config?.headers
  if (!headers) return false
  return Boolean(
    headerAuthorization(headers) || headerAuthorization(headers.common)
  )
}

export function shouldMarkAuthUnauthorized(status, config) {
  if (Number(status) !== 401) return false
  const requestUrl = String(config?.url || '')
  if (requestUrl.includes('/api/auth/')) return false
  // Browser <img> and tokenless cover fetches 401 when auth is on. That must
  // not sign family users out while Library JSON still used a valid token.
  return requestHasAuthorization(config)
}

export function markAuthUnauthorized() {
  const profiles = status.value.profiles
  applyAuthStatus({
    auth_required: true,
    setup_required: false,
    authenticated: false,
    user: null,
    profiles,
  })
  clearAuthToken()
}

export function authHeaders() {
  const token = getStoredAuthToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export function useAuthSession() {
  const user = computed(() => status.value.user)
  const needsAuthGate = computed(
    () =>
      ready.value &&
      (status.value.setup_required ||
        (status.value.auth_required && !status.value.authenticated))
  )
  const isAdmin = computed(() => Boolean(user.value?.is_admin))
  const isFamilyUser = computed(() => Boolean(user.value) && !isAdmin.value)
  const canUseAdminPages = computed(() => {
    if (isFamilyUser.value) return false
    return !status.value.auth_required || isAdmin.value
  })
  return {
    status,
    user,
    loading,
    errorMessage,
    ready,
    needsAuthGate,
    isAdmin,
    isFamilyUser,
    canUseAdminPages,
    profiles: computed(() => status.value.profiles),
  }
}

export { status as authStatus, ready }
