import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useLibraryRefresh } from '../model/libraryRefresh'

describe('useLibraryRefresh', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    const libraryRefresh = useLibraryRefresh()
    libraryRefresh.setLoading(false)
    libraryRefresh.setFailed(false)
    libraryRefresh.unregister()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('shows the spinner for a minimum duration even when the refresh is instant', async () => {
    const libraryRefresh = useLibraryRefresh()
    let calls = 0
    libraryRefresh.register(async () => {
      calls += 1
    })

    const done = libraryRefresh.refresh()
    // Loading turns on synchronously so the spinner appears immediately.
    expect(libraryRefresh.loading.value).toBe(true)

    await vi.runAllTimersAsync()
    await done

    expect(calls).toBe(1)
    expect(libraryRefresh.loading.value).toBe(false)
    expect(libraryRefresh.failed.value).toBe(false)
  })

  it('surfaces failures reported by the handler', async () => {
    const libraryRefresh = useLibraryRefresh()
    libraryRefresh.register(async () => {
      libraryRefresh.setFailed(true)
    })

    const done = libraryRefresh.refresh()
    await vi.runAllTimersAsync()
    await done

    expect(libraryRefresh.loading.value).toBe(false)
    expect(libraryRefresh.failed.value).toBe(true)
  })

  it('clears a previous failure when a new refresh starts', async () => {
    const libraryRefresh = useLibraryRefresh()
    libraryRefresh.setFailed(true)
    libraryRefresh.register(async () => {})

    const done = libraryRefresh.refresh()
    expect(libraryRefresh.failed.value).toBe(false)

    await vi.runAllTimersAsync()
    await done
  })

  it('does nothing when no handler is registered', async () => {
    const libraryRefresh = useLibraryRefresh()
    await libraryRefresh.refresh()
    expect(libraryRefresh.loading.value).toBe(false)
  })

  it('ignores re-entrant refreshes while one is in flight', async () => {
    const libraryRefresh = useLibraryRefresh()
    let calls = 0
    libraryRefresh.register(async () => {
      calls += 1
    })

    const first = libraryRefresh.refresh()
    const second = libraryRefresh.refresh()

    await vi.runAllTimersAsync()
    await Promise.all([first, second])

    expect(calls).toBe(1)
  })
})
