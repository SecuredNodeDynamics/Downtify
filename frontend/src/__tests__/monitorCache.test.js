import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@capacitor/core', () => ({
  Capacitor: {
    isNativePlatform: vi.fn(() => false),
    isPluginAvailable: vi.fn(() => false),
  },
}))

import { applyAuthStatus } from '../model/authSession.js'
import { monitorListCacheKey } from '../model/monitor.js'

describe('monitor list cache', () => {
  beforeEach(() => {
    applyAuthStatus({
      auth_required: true,
      setup_required: false,
      authenticated: false,
      user: null,
      profiles: [],
    })
  })

  afterEach(() => {
    applyAuthStatus({
      auth_required: false,
      setup_required: false,
      authenticated: false,
      user: null,
      profiles: [],
    })
  })

  it('keys the playlist cache by server and signed-in user', () => {
    const anonKey = monitorListCacheKey()
    applyAuthStatus({
      auth_required: true,
      authenticated: true,
      user: { id: 1, username: 'Artyom' },
      profiles: [],
    })
    const artyomKey = monitorListCacheKey()
    applyAuthStatus({
      auth_required: true,
      authenticated: true,
      user: { id: 2, username: 'kid' },
      profiles: [],
    })
    const kidKey = monitorListCacheKey()

    expect(artyomKey).not.toBe(anonKey)
    expect(kidKey).not.toBe(artyomKey)
    expect(artyomKey).toContain('artyom')
    expect(kidKey).toContain('kid')
  })
})
