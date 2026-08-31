import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('@capacitor/core', () => ({
  Capacitor: {
    isNativePlatform: vi.fn(() => false),
    isPluginAvailable: vi.fn(() => false),
  },
}))

import { Capacitor } from '@capacitor/core'
import {
  buildApiBaseUrl,
  canSaveServerUrlInput,
  classifyServerUrl,
  getActiveServerRoute,
  getCurrentPageServerUrl,
  getConnectionMode,
  getStoredPrivateServerUrl,
  getStoredPublicServerUrl,
  getStoredServerUrl,
  isConnectedToCurrentPage,
  parseServerUrl,
  repairStoredServerUrl,
  setActiveServerRoute,
  setStoredPrivateServerUrl,
  setStoredPublicServerUrl,
  setStoredServerUrl,
} from '../model/serverConnection.js'

describe('serverConnection', () => {
  it('parses a LAN Docker host without treating it as the phone loopback', () => {
    const cfg = parseServerUrl('http://10.128.1.63:8000')
    expect(cfg).toEqual({
      PROTOCOL: 'http:',
      WS_PROTOCOL: 'ws:',
      BACKEND: '10.128.1.63',
      PORT: '8000',
      BASEURL: '',
    })
    expect(buildApiBaseUrl(cfg)).toBe('http://10.128.1.63:8000')
  })

  it('parses https tunnel URLs without explicit port', () => {
    const cfg = parseServerUrl('https://downtify.example.com')
    expect(cfg).toEqual({
      PROTOCOL: 'https:',
      WS_PROTOCOL: 'wss:',
      BACKEND: 'downtify.example.com',
      PORT: '',
      BASEURL: '',
    })
    expect(buildApiBaseUrl(cfg)).toBe('https://downtify.example.com')
  })

  it('parses LAN host:port addresses', () => {
    const cfg = parseServerUrl('192.168.1.50:8765')
    expect(cfg).toEqual({
      PROTOCOL: 'http:',
      WS_PROTOCOL: 'ws:',
      BACKEND: '192.168.1.50',
      PORT: '8765',
      BASEURL: '',
    })
    expect(buildApiBaseUrl(cfg)).toBe('http://192.168.1.50:8765')
  })

  it('preserves optional base paths', () => {
    const cfg = parseServerUrl('https://downtify.example.com/app/')
    expect(cfg?.BASEURL).toBe('/app')
    expect(buildApiBaseUrl(cfg)).toBe('https://downtify.example.com/app')
  })

  it('rejects invalid addresses', () => {
    expect(parseServerUrl('')).toBeNull()
    expect(parseServerUrl('   ')).toBeNull()
    expect(parseServerUrl('not a url')).toBeNull()
  })

  it('getCurrentPageServerUrl uses origin not SPA route path', () => {
    vi.stubGlobal('window', {
      location: {
        protocol: 'http:',
        hostname: '192.168.1.50',
        port: '8765',
        pathname: '/monitor',
      },
    })
    expect(getCurrentPageServerUrl()).toBe('http://192.168.1.50:8765')
  })

  it('treats Capacitor native as having no current-page server', () => {
    Capacitor.isNativePlatform.mockReturnValue(true)
    vi.stubGlobal('window', {
      location: {
        protocol: 'https:',
        hostname: 'localhost',
        port: '',
        pathname: '/settings',
      },
    })
    expect(getCurrentPageServerUrl()).toBe('')
    expect(isConnectedToCurrentPage()).toBe(false)
  })

  it('repairs stored URLs that mistakenly include SPA route paths', () => {
    const storage = {}
    vi.stubGlobal('localStorage', {
      getItem: (key) => storage[key] ?? null,
      setItem: (key, value) => {
        storage[key] = value
      },
      removeItem: (key) => {
        delete storage[key]
      },
    })
    storage['downtify-server-url'] = 'http://192.168.1.50:8765/monitor'
    repairStoredServerUrl()
    expect(storage['downtify-server-url']).toBe('http://192.168.1.50:8765')
  })

  it('allows saving when the typed URL differs from the active config', () => {
    vi.stubGlobal('window', {
      location: {
        protocol: 'http:',
        hostname: 'localhost',
        port: '5173',
        pathname: '/settings',
      },
    })
    expect(canSaveServerUrlInput('http://localhost:8000')).toBe(true)
    expect(canSaveServerUrlInput('http://localhost:5173')).toBe(false)
  })

  it('allows saving a new custom URL while browsing another origin', () => {
    const storage = {}
    vi.stubGlobal('localStorage', {
      getItem: (key) => storage[key] ?? null,
      setItem: (key, value) => {
        storage[key] = value
      },
      removeItem: (key) => {
        delete storage[key]
      },
    })
    vi.stubGlobal('window', {
      location: {
        protocol: 'http:',
        hostname: 'localhost',
        port: '5173',
        pathname: '/settings',
      },
    })
    storage['downtify-server-url'] = 'http://localhost:8000'
    expect(canSaveServerUrlInput('http://localhost:8000')).toBe(false)
    expect(canSaveServerUrlInput('http://127.0.0.1:8000')).toBe(true)
  })

  it('defaults the APK to a saved LAN or tunnel URL instead of 127.0.0.1', () => {
    const storage = {
      'downtify-server-url': 'https://downtify.janzenmediagroup.com',
    }
    vi.stubGlobal('localStorage', {
      getItem: (key) => storage[key] ?? null,
      setItem: (key, value) => {
        storage[key] = value
      },
      removeItem: (key) => {
        delete storage[key]
      },
    })
    Capacitor.isNativePlatform.mockReturnValue(true)
    Capacitor.isPluginAvailable.mockReturnValue(true)

    expect(getConnectionMode()).toBe('server')
  })

  it('keeps an explicit on-device mode even when a server URL is saved', () => {
    const storage = {
      'downtify-server-url': 'http://10.128.1.63:8000',
      'downtify-connection-mode': 'device',
    }
    vi.stubGlobal('localStorage', {
      getItem: (key) => storage[key] ?? null,
      setItem: (key, value) => {
        storage[key] = value
      },
      removeItem: (key) => {
        delete storage[key]
      },
    })
    Capacitor.isNativePlatform.mockReturnValue(true)
    Capacitor.isPluginAvailable.mockReturnValue(true)

    expect(getConnectionMode()).toBe('device')
  })

  it('classifies LAN IPs as private and hostnames as public', () => {
    expect(classifyServerUrl('http://10.128.1.63:8000')).toBe('private')
    expect(classifyServerUrl('192.168.1.50:8765')).toBe('private')
    expect(classifyServerUrl('https://downtify.janzenmediagroup.com')).toBe(
      'public'
    )
  })

  it('migrates a saved LAN URL into the private slot', () => {
    const storage = {
      'downtify-server-url': 'http://10.128.1.63:8000',
    }
    vi.stubGlobal('localStorage', {
      getItem: (key) => storage[key] ?? null,
      setItem: (key, value) => {
        storage[key] = value
      },
      removeItem: (key) => {
        delete storage[key]
      },
    })
    expect(getStoredServerUrl()).toBe('http://10.128.1.63:8000')
    expect(getStoredPrivateServerUrl()).toBe('http://10.128.1.63:8000')
    expect(getStoredPublicServerUrl()).toBe('')
    expect(getActiveServerRoute()).toBe('private')
  })

  it('keeps private and public URLs and switches the active one', () => {
    const storage = {}
    vi.stubGlobal('localStorage', {
      getItem: (key) => storage[key] ?? null,
      setItem: (key, value) => {
        storage[key] = value
      },
      removeItem: (key) => {
        delete storage[key]
      },
    })
    setStoredPrivateServerUrl('http://10.128.1.63:8000')
    setStoredPublicServerUrl('https://downtify.janzenmediagroup.com')
    setActiveServerRoute('private')
    expect(getStoredServerUrl()).toBe('http://10.128.1.63:8000')
    setActiveServerRoute('public')
    expect(getStoredServerUrl()).toBe('https://downtify.janzenmediagroup.com')
    expect(getStoredPrivateServerUrl()).toBe('http://10.128.1.63:8000')
    expect(getActiveServerRoute()).toBe('public')
  })

  afterEach(() => {
    Capacitor.isNativePlatform.mockReturnValue(false)
    Capacitor.isPluginAvailable.mockReturnValue(false)
    vi.unstubAllGlobals()
  })
})
