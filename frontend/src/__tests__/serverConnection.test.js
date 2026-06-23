import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('@capacitor/core', () => ({
  Capacitor: {
    isNativePlatform: vi.fn(() => false),
  },
}))

import { Capacitor } from '@capacitor/core'
import {
  buildApiBaseUrl,
  canSaveServerUrlInput,
  getCurrentPageServerUrl,
  isConnectedToCurrentPage,
  parseServerUrl,
  repairStoredServerUrl,
  setStoredServerUrl,
} from '../model/serverConnection.js'

describe('serverConnection', () => {
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

  afterEach(() => {
    Capacitor.isNativePlatform.mockReturnValue(false)
    vi.unstubAllGlobals()
  })
})
