import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('../model/api.js', () => ({
  default: {
    getLibraryGenresStatus: vi.fn(),
    startLibraryGenreRefresh: vi.fn(),
    cancelLibraryGenreRefresh: vi.fn(),
  },
}))

vi.mock('../model/librarySession.js', () => ({
  notifyLibraryChanged: vi.fn(),
}))

import API from '../model/api.js'
import {
  ensureLibraryGenreLookup,
  genreWarmupPercent,
  isGenreWarmupRunning,
  isGenreWarmupStalled,
  resetGenreLookupMemory,
} from '../model/genreRefresh.js'

describe('genre refresh', () => {
  afterEach(() => {
    resetGenreLookupMemory()
    vi.clearAllMocks()
  })

  it('treats running warmup as in progress', () => {
    expect(isGenreWarmupRunning({ status: 'running' })).toBe(true)
    expect(isGenreWarmupRunning({ status: 'complete' })).toBe(false)
  })

  it('starts a genre lookup when tracks are still untagged', async () => {
    API.getLibraryGenresStatus.mockResolvedValue({ data: { status: 'idle' } })
    API.startLibraryGenreRefresh.mockResolvedValue({
      data: { status: 'running' },
    })
    await ensureLibraryGenreLookup(4)
    expect(API.startLibraryGenreRefresh).toHaveBeenCalledTimes(1)
  })

  it('does not restart after a completed lookup for the same unknown count', async () => {
    API.getLibraryGenresStatus
      .mockResolvedValueOnce({ data: { status: 'idle' } })
      .mockResolvedValue({ data: { status: 'complete' } })
    API.startLibraryGenreRefresh.mockResolvedValue({
      data: { status: 'running' },
    })
    await ensureLibraryGenreLookup(4)
    await ensureLibraryGenreLookup(4)
    expect(API.startLibraryGenreRefresh).toHaveBeenCalledTimes(1)
  })

  it('does not auto-restart after the user stops a lookup', async () => {
    API.getLibraryGenresStatus.mockResolvedValue({
      data: { status: 'cancelled' },
    })
    await ensureLibraryGenreLookup(12)
    expect(API.startLibraryGenreRefresh).not.toHaveBeenCalled()
  })

  it('reports lookup percent and stall state', () => {
    expect(genreWarmupPercent({ current: 5, total: 20 })).toBe(25)
    expect(
      isGenreWarmupStalled({
        status: 'running',
        phase: 'artists',
        updated_at: new Date(Date.now() - 60_000).toISOString(),
      })
    ).toBe(true)
    expect(
      isGenreWarmupStalled({
        status: 'running',
        phase: 'library',
        updated_at: new Date(Date.now() - 60_000).toISOString(),
      })
    ).toBe(false)
  })
})
