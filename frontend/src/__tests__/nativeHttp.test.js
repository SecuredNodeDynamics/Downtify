import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@capacitor/core', () => ({
  Capacitor: {
    isNativePlatform: vi.fn(() => true),
  },
  CapacitorHttp: {
    request: vi.fn(),
  },
}))

vi.mock('../model/serverConnection.js', () => ({
  isCapacitorNative: vi.fn(() => true),
}))

import { CapacitorHttp } from '@capacitor/core'
import { isCapacitorNative } from '../model/serverConnection.js'
import {
  capacitorAxiosAdapter,
  requestPath,
  shouldUseNativeHttpAdapter,
} from '../model/nativeHttp.js'

describe('nativeHttp', () => {
  beforeEach(() => {
    isCapacitorNative.mockReturnValue(true)
    CapacitorHttp.request.mockReset()
  })

  it('keeps large library payloads on the WebView adapter', () => {
    expect(
      shouldUseNativeHttpAdapter({
        url: '/api/library/files',
        baseURL: 'https://downtify.example.com',
      })
    ).toBe(false)
    expect(
      shouldUseNativeHttpAdapter({
        url: '/list',
        baseURL: 'http://10.128.1.63:8000',
      })
    ).toBe(false)
  })

  it('uses native HTTP for small authenticated API calls', () => {
    expect(
      shouldUseNativeHttpAdapter({
        url: '/api/auth/status',
        baseURL: 'https://downtify.example.com',
      })
    ).toBe(true)
    expect(
      shouldUseNativeHttpAdapter({
        url: '/api/version',
        baseURL: 'http://10.128.1.63:8000',
      })
    ).toBe(true)
  })

  it('resolves relative URLs against the API origin', () => {
    expect(
      requestPath({
        url: '/api/auth/status',
        baseURL: 'https://downtify.example.com',
      })
    ).toBe('/api/auth/status')
  })

  it('maps Capacitor HTTP responses onto axios responses', async () => {
    CapacitorHttp.request.mockResolvedValue({
      status: 200,
      data: { ok: true },
      headers: { 'content-type': 'application/json' },
    })

    const result = await capacitorAxiosAdapter({
      url: '/api/version',
      baseURL: 'https://downtify.example.com',
      method: 'get',
      timeout: 8000,
      headers: { Authorization: 'Bearer token' },
    })

    expect(CapacitorHttp.request).toHaveBeenCalledWith(
      expect.objectContaining({
        url: 'https://downtify.example.com/api/version',
        method: 'GET',
        connectTimeout: 8000,
        headers: { Authorization: 'Bearer token' },
      })
    )
    expect(result.status).toBe(200)
    expect(result.data).toEqual({ ok: true })
  })

  it('rejects non-2xx Capacitor responses as axios errors', async () => {
    CapacitorHttp.request.mockResolvedValue({
      status: 401,
      data: { detail: 'unauthorized' },
      headers: {},
    })

    await expect(
      capacitorAxiosAdapter({
        url: '/api/auth/status',
        baseURL: 'https://downtify.example.com',
        method: 'get',
      })
    ).rejects.toMatchObject({
      response: { status: 401 },
    })
  })
})
