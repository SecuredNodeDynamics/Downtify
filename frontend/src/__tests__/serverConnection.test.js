import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  buildApiBaseUrl,
  getCurrentPageServerUrl,
  parseServerUrl,
  repairStoredServerUrl,
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

  afterEach(() => {
    vi.unstubAllGlobals()
  })
})
