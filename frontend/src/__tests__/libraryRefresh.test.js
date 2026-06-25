import { describe, expect, it } from 'vitest'

import { useLibraryRefresh } from '../model/libraryRefresh'

describe('useLibraryRefresh', () => {
  it('tracks loading and failure state for header refresh', async () => {
    const libraryRefresh = useLibraryRefresh()
    let calls = 0

    libraryRefresh.register(async () => {
      calls += 1
      libraryRefresh.setLoading(true)
      libraryRefresh.setFailed(true)
      libraryRefresh.setLoading(false)
    })

    await libraryRefresh.refresh()

    expect(calls).toBe(1)
    expect(libraryRefresh.loading.value).toBe(false)
    expect(libraryRefresh.failed.value).toBe(true)
  })

  it('clears failed state when a new refresh starts', async () => {
    const libraryRefresh = useLibraryRefresh()
    libraryRefresh.setFailed(true)

    libraryRefresh.register(async () => {})

    await libraryRefresh.refresh()

    expect(libraryRefresh.failed.value).toBe(false)
  })
})
