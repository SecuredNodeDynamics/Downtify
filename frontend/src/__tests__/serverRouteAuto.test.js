import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('@capacitor/core', () => ({
  Capacitor: {
    isNativePlatform: vi.fn(() => true),
    isPluginAvailable: vi.fn(() => false),
  },
  CapacitorHttp: {
    request: vi.fn(),
  },
}))

import { Capacitor, CapacitorHttp } from '@capacitor/core'
import {
  getActiveServerRoute,
  getStoredServerUrl,
  setStoredPrivateServerUrl,
  setStoredPublicServerUrl,
  setActiveServerRoute,
} from '../model/serverConnection.js'
import {
  applyPreferredServerRoute,
  choosePreferredServerRoute,
  failOverToPublicServerRoute,
} from '../model/serverRouteAuto.js'

function mockStorage(initial = {}) {
  const storage = { ...initial }
  vi.stubGlobal('localStorage', {
    getItem: (key) => storage[key] ?? null,
    setItem: (key, value) => {
      storage[key] = value
    },
    removeItem: (key) => {
      delete storage[key]
    },
  })
  return storage
}

describe('server route auto switch', () => {
  afterEach(() => {
    Capacitor.isNativePlatform.mockReturnValue(true)
    Capacitor.isPluginAvailable.mockReturnValue(false)
    CapacitorHttp.request.mockReset()
    vi.unstubAllGlobals()
  })

  it('prefers the home network when it is reachable', () => {
    expect(
      choosePreferredServerRoute({
        privateUrl: 'http://10.128.1.63:8000',
        publicUrl: 'https://downtify.example.com',
        privateReachable: true,
      })
    ).toBe('private')
  })

  it('uses Cloudflare when the home network is not reachable', () => {
    expect(
      choosePreferredServerRoute({
        privateUrl: 'http://10.128.1.63:8000',
        publicUrl: 'https://downtify.example.com',
        privateReachable: false,
      })
    ).toBe('public')
  })

  it('switches the active route to Cloudflare after a LAN probe miss', async () => {
    mockStorage()
    setStoredPrivateServerUrl('http://10.128.1.63:8000')
    setStoredPublicServerUrl('https://downtify.example.com')
    setActiveServerRoute('private')
    CapacitorHttp.request.mockResolvedValue({
      status: 0,
      data: '',
    })

    const changed = await applyPreferredServerRoute()
    expect(changed).toBe(true)
    expect(getActiveServerRoute()).toBe('public')
    expect(getStoredServerUrl()).toBe('https://downtify.example.com')
  })

  it('keeps Home network when the LAN health check succeeds', async () => {
    mockStorage()
    setStoredPrivateServerUrl('http://10.128.1.63:8000')
    setStoredPublicServerUrl('https://downtify.example.com')
    setActiveServerRoute('public')
    CapacitorHttp.request.mockResolvedValue({
      status: 200,
      data: { status: 'ok' },
    })

    const changed = await applyPreferredServerRoute()
    expect(changed).toBe(true)
    expect(getActiveServerRoute()).toBe('private')
  })

  it('fails over from LAN to Cloudflare without a probe', () => {
    mockStorage()
    setStoredPrivateServerUrl('http://10.128.1.63:8000')
    setStoredPublicServerUrl('https://downtify.example.com')
    setActiveServerRoute('private')
    expect(failOverToPublicServerRoute()).toBe(true)
    expect(getActiveServerRoute()).toBe('public')
  })
})
