import { computed, ref } from 'vue'

import { buildApiBaseUrl, getServerConfig } from './serverConnection.js'

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

export function getStoredAuthToken(baseUrl) {
  if (typeof localStorage === 'undefined') return ''
  try {
    return localStorage.getItem(sessionStorageKey(baseUrl)) || ''
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
  const canUseAdminPages = computed(
    () => !status.value.auth_required || isAdmin.value
  )
  return {
    status,
    user,
    loading,
    errorMessage,
    ready,
    needsAuthGate,
    isAdmin,
    canUseAdminPages,
    profiles: computed(() => status.value.profiles),
  }
}

export { status as authStatus, ready }
