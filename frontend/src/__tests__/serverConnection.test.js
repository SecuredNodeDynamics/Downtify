import { describe, expect, it } from 'vitest'
import {
  buildApiBaseUrl,
  parseServerUrl,
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
})
