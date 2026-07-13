import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  beginAppLoading,
  endAppLoading,
  resetAppLoading,
  useAppLoading,
} from '../model/appLoading.js'

describe('appLoading', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    resetAppLoading()
  })

  afterEach(() => {
    resetAppLoading()
    vi.useRealTimers()
  })

  it('shows the overlay only after a short delay', () => {
    const { visible } = useAppLoading()

    beginAppLoading()
    expect(visible.value).toBe(false)

    vi.advanceTimersByTime(519)
    expect(visible.value).toBe(false)

    vi.advanceTimersByTime(1)
    expect(visible.value).toBe(true)
  })

  it('hides the overlay after work completes', () => {
    const { visible } = useAppLoading()

    beginAppLoading()
    vi.advanceTimersByTime(520)
    endAppLoading()
    vi.advanceTimersByTime(220)

    expect(visible.value).toBe(false)
  })
})
