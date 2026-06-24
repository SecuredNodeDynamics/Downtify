import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@capacitor/core', () => ({
  Capacitor: {
    isNativePlatform: vi.fn(),
  },
}))

import { Capacitor } from '@capacitor/core'

import {
  getStoredServerUrl,
  setStoredServerUrl,
} from '../model/serverConnection.js'
import { usesApkUpdateFlow, usesServerUpdateFlow } from '../model/appUpdate.js'

describe('appUpdate flows', () => {
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
    setStoredServerUrl('')
  })

  afterEach(() => {
    setStoredServerUrl('')
    vi.unstubAllGlobals()
  })
  it('uses the server/docker update flow in the browser', () => {
    Capacitor.isNativePlatform.mockReturnValue(false)
    setStoredServerUrl('')

    expect(usesServerUpdateFlow()).toBe(true)
    expect(usesApkUpdateFlow()).toBe(false)
  })

  it('uses the APK update flow for the standalone native app shell', () => {
    Capacitor.isNativePlatform.mockReturnValue(true)
    setStoredServerUrl('')

    expect(usesServerUpdateFlow()).toBe(false)
    expect(usesApkUpdateFlow()).toBe(true)
  })

  it('uses the APK update flow when the native app targets a remote server', () => {
    Capacitor.isNativePlatform.mockReturnValue(true)
    setStoredServerUrl('http://10.128.1.63:8000')

    expect(usesServerUpdateFlow()).toBe(false)
    expect(usesApkUpdateFlow()).toBe(true)
    expect(getStoredServerUrl()).toBe('http://10.128.1.63:8000')
  })
})
