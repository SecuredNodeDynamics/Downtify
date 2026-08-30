import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { waitForEmbeddedServer } from '../model/embeddedServer.js'

describe('waitForEmbeddedServer', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('returns true when /api/version becomes reachable', async () => {
    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(new Error('connection refused'))
      .mockResolvedValueOnce({ ok: true })
    vi.stubGlobal('fetch', fetchMock)

    const pending = waitForEmbeddedServer('http://127.0.0.1:8765', {
      attempts: 5,
      delayMs: 20,
    })
    await vi.advanceTimersByTimeAsync(20)
    await expect(pending).resolves.toBe(true)
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('does not wait forever when a version request hangs', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(
        (_url, { signal } = {}) =>
          new Promise((_, reject) => {
            const fail = () =>
              reject(
                Object.assign(new Error('aborted'), { name: 'AbortError' })
              )
            if (signal?.aborted) fail()
            else signal?.addEventListener('abort', fail)
          })
      )
    )

    const pending = waitForEmbeddedServer('http://127.0.0.1:8765', {
      attempts: 1,
      delayMs: 0,
      fetchTimeoutMs: 40,
    })
    await vi.advanceTimersByTimeAsync(40)
    await expect(pending).resolves.toBe(false)
  })
})
