import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('@capacitor/core', () => ({
  Capacitor: {
    isNativePlatform: vi.fn(() => false),
    isPluginAvailable: vi.fn(() => false),
  },
}))

import {
  clearAuthToken,
  getStoredAuthToken,
  sessionStorageKey,
  storeAuthToken,
} from '../model/authSession.js'

describe('authSession', () => {
  const storage = {}

  afterEach(() => {
    for (const key of Object.keys(storage)) delete storage[key]
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
})
