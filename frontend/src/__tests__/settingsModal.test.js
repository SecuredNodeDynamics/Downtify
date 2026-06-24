import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const { push, back, currentRoute } = vi.hoisted(() => ({
  push: vi.fn(),
  back: vi.fn(),
  currentRoute: { value: { name: 'Home' } },
}))

vi.mock('../router', () => ({
  default: {
    push,
    back,
    currentRoute,
  },
}))

import {
  closeSettingsModal,
  isSettingsModalOpen,
  openSettings,
  openSettingsModal,
} from '../model/settingsModal.js'

describe('settingsModal', () => {
  beforeEach(() => {
    vi.stubGlobal('window', {
      dispatchEvent: vi.fn(),
      history: { length: 2 },
    })
  })

  afterEach(() => {
    push.mockClear()
    back.mockClear()
    currentRoute.value = { name: 'Home' }
    vi.unstubAllGlobals()
  })

  it('navigates to the settings page', () => {
    openSettings()
    expect(push).toHaveBeenCalledWith({ name: 'Settings', query: {} })
  })

  it('opens a specific settings tab via query', () => {
    openSettingsModal('api')
    expect(push).toHaveBeenCalledWith({
      name: 'Settings',
      query: { tab: 'api' },
    })
  })

  it('dispatches downtify:open-settings when a tab is provided', () => {
    let detail = null
    const listeners = new Map()
    vi.stubGlobal('window', {
      dispatchEvent: (event) => {
        listeners.get(event.type)?.(event)
        return true
      },
      addEventListener: (type, handler) => {
        listeners.set(type, handler)
      },
      removeEventListener: (type) => {
        listeners.delete(type)
      },
      history: { length: 2 },
    })
    window.addEventListener('downtify:open-settings', (event) => {
      detail = event.detail
    })
    openSettings('help')
    expect(detail).toEqual({ tab: 'help' })
  })

  it('reports when settings route is active', () => {
    currentRoute.value = { name: 'Settings' }
    expect(isSettingsModalOpen()).toBe(true)
    currentRoute.value = { name: 'Home' }
    expect(isSettingsModalOpen()).toBe(false)
  })

  it('closes settings by navigating back', () => {
    vi.stubGlobal('window', { history: { length: 2 } })
    closeSettingsModal()
    expect(back).toHaveBeenCalled()
  })
})
