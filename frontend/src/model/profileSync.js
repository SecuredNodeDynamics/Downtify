import { AUTH_CHANGED_EVENT } from './authSession.js'

export const PROFILE_SYNCED_EVENT = 'downtify:profile-synced'

const BUNDLE_PREFIX = 'downtify-profile-bundle:'

function storage() {
  if (typeof localStorage === 'undefined') return null
  return localStorage
}

export function profileBundleKey(user) {
  const profileKey = String(user?.profile_key || '').trim()
  if (profileKey) return `${BUNDLE_PREFIX}key:${profileKey}`
  const username = String(user?.username || '')
    .trim()
    .toLowerCase()
  if (username) return `${BUNDLE_PREFIX}user:${username}`
  return ''
}

export function loadProfileBundle(user) {
  const store = storage()
  if (!store) return null
  const keys = [
    profileBundleKey(user),
    user?.username
      ? `${BUNDLE_PREFIX}user:${String(user.username).trim().toLowerCase()}`
      : '',
  ].filter(Boolean)
  for (const key of keys) {
    try {
      const parsed = JSON.parse(store.getItem(key) || 'null')
      if (parsed && typeof parsed === 'object') return parsed
    } catch {
      // ignore bad cache
    }
  }
  return null
}

export function storeProfileBundle(bundle) {
  const store = storage()
  if (!store || !bundle || typeof bundle !== 'object') return
  const keys = [
    profileBundleKey(bundle),
    bundle.username
      ? `${BUNDLE_PREFIX}user:${String(bundle.username).trim().toLowerCase()}`
      : '',
  ].filter(Boolean)
  const payload = JSON.stringify({
    profile_key: String(bundle.profile_key || ''),
    username: String(bundle.username || ''),
    display_name: String(bundle.display_name || bundle.username || ''),
    monitors: Array.isArray(bundle.monitors) ? bundle.monitors : [],
    groups: Array.isArray(bundle.groups) ? bundle.groups : [],
    saved_at: new Date().toISOString(),
  })
  for (const key of keys) {
    try {
      store.setItem(key, payload)
    } catch {
      // ignore quota
    }
  }
}

export function notifyProfileSynced(detail) {
  if (typeof window === 'undefined') return
  window.dispatchEvent(
    new CustomEvent(PROFILE_SYNCED_EVENT, { detail: detail || {} })
  )
  window.dispatchEvent(
    new CustomEvent(AUTH_CHANGED_EVENT, { detail: detail || {} })
  )
}
