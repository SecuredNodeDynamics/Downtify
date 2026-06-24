import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@capacitor/app', () => ({
  App: {
    getInfo: vi.fn(),
  },
}))

vi.mock('@capacitor/core', () => ({
  Capacitor: {
    isNativePlatform: vi.fn(),
  },
  registerPlugin: vi.fn(() => ({})),
}))

import { App } from '@capacitor/app'
import { Capacitor } from '@capacitor/core'

import {
  getBundledAppVersion,
  getInstalledClientVersionSync,
  readCachedServerVersion,
  resolveNativeInstalledVersion,
  writeCachedServerVersion,
} from '../model/appVersion.js'

describe('appVersion', () => {
  beforeEach(() => {
    const store = new Map()
    vi.stubGlobal('localStorage', {
      getItem: (key) => store.get(key) ?? null,
      setItem: (key, value) => {
        store.set(key, value)
      },
      removeItem: (key) => {
        store.delete(key)
      },
      clear: () => {
        store.clear()
      },
    })
    Capacitor.isNativePlatform.mockReturnValue(false)
    App.getInfo.mockReset()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('reads the bundled web version from the build-time constant', () => {
    expect(getBundledAppVersion()).toMatch(/^\d+\.\d+\.\d+$/)
  })

  it('stores the connected server version for mismatch checks', () => {
    writeCachedServerVersion('2.10.57')
    expect(readCachedServerVersion()).toBe('2.10.57')
  })

  it('uses the native Android version name when available', async () => {
    Capacitor.isNativePlatform.mockReturnValue(true)
    App.getInfo.mockResolvedValue({ version: '2.10.55', build: '21055' })

    await expect(resolveNativeInstalledVersion()).resolves.toBe('2.10.55')
    expect(getInstalledClientVersionSync()).toBe('2.10.55')
  })
})
