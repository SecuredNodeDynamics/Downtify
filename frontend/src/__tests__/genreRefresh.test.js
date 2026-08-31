import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('../model/api.js', () => ({
  default: {
    getLibraryGenresStatus: vi.fn(),
    startLibraryGenreRefresh: vi.fn(),
  },
}))

import API from '../model/api.js'
import {
  ensureLibraryGenreLookup,
  isGenreWarmupRunning,
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
})
