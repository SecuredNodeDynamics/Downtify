import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('@capacitor/core', () => ({
  Capacitor: {
    isNativePlatform: vi.fn(() => false),
    isPluginAvailable: vi.fn(() => false),
  },
}))

import {
  applyAuthStatus,
  clearAuthToken,
  getStoredAuthToken,
  sessionStorageKey,
  shouldMarkAuthUnauthorized,
  storeAuthToken,
  useAuthSession,
} from '../model/authSession.js'

describe('authSession', () => {
  const storage = {}

  afterEach(() => {
    for (const key of Object.keys(storage)) delete storage[key]
    applyAuthStatus({
      auth_required: false,
      setup_required: false,
      authenticated: false,
      user: null,
      profiles: [],
    })
  })

  it('stores tokens per backend URL', () => {
    vi.stubGlobal('localStorage', {
      getItem: (key) => storage[key] ?? null,
      setItem: (key, value) => {
        storage[key] = value
      },
      removeItem: (key) => {
        delete storage[key]
      },
    })
    storeAuthToken('server-token', 'http://10.128.1.63:8000')
    storeAuthToken('device-token', 'http://127.0.0.1:8765')

    expect(sessionStorageKey('http://10.128.1.63:8000')).toBe(
      'downtify-session-token:http://10.128.1.63:8000'
    )
    expect(getStoredAuthToken('http://10.128.1.63:8000')).toBe('server-token')
    expect(getStoredAuthToken('http://127.0.0.1:8765')).toBe('device-token')
    clearAuthToken('http://10.128.1.63:8000')
    expect(getStoredAuthToken('http://10.128.1.63:8000')).toBe('')
  })

  it('reuses a login token between home network and Cloudflare URLs', () => {
    vi.stubGlobal('localStorage', {
      getItem: (key) => storage[key] ?? null,
      setItem: (key, value) => {
        storage[key] = value
      },
      removeItem: (key) => {
        delete storage[key]
      },
    })
    storage['downtify-server-url-private'] = 'http://10.128.1.63:8000'
    storage['downtify-server-url-public'] =
      'https://downtify.janzenmediagroup.com'
    storeAuthToken('shared-token', 'http://10.128.1.63:8000')
    expect(getStoredAuthToken('https://downtify.janzenmediagroup.com')).toBe(
      'shared-token'
    )
  })

  it('does not treat tokenless 401s as a signed-out session', () => {
    expect(shouldMarkAuthUnauthorized(401, { url: '/api/library/files' })).toBe(
      false
    )
    expect(
      shouldMarkAuthUnauthorized(401, {
        url: '/api/library/artist-cover',
        headers: { Authorization: 'Bearer family-token' },
      })
    ).toBe(true)
    expect(
      shouldMarkAuthUnauthorized(403, {
        url: '/api/metadata/scan',
        headers: { Authorization: 'Bearer family-token' },
      })
    ).toBe(false)
  })

  it('hides admin settings for family profiles', () => {
    applyAuthStatus({
      auth_required: true,
      setup_required: false,
      authenticated: true,
      user: { username: 'kid', is_admin: false },
      profiles: [],
    })
    const { isAdmin, isFamilyUser, canUseAdminPages } = useAuthSession()
    expect(isAdmin.value).toBe(false)
    expect(isFamilyUser.value).toBe(true)
    expect(canUseAdminPages.value).toBe(false)
  })

  it('hides admin settings for family even if auth_required is unset', () => {
    applyAuthStatus({
      authenticated: true,
      user: { username: 'kid', is_admin: false },
    })
    const { canUseAdminPages } = useAuthSession()
    expect(canUseAdminPages.value).toBe(false)
  })

  it('keeps admin settings when login is not required', () => {
    applyAuthStatus({
      auth_required: false,
      authenticated: false,
      user: null,
    })
    const { canUseAdminPages, isFamilyUser } = useAuthSession()
    expect(isFamilyUser.value).toBe(false)
    expect(canUseAdminPages.value).toBe(true)
  })
})
