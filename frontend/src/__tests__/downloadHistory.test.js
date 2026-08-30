import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../model/api', () => ({
  default: {
    getHistory: vi.fn(),
    reconcileHistory: vi.fn(),
  },
}))

import API from '../model/api'
import {
  clearDownloadHistoryState,
  markHistoryRetrying,
  refreshDownloadHistory,
  upsertHistoryItem,
  useDownloadHistory,
} from '../model/downloadHistory.js'

describe('download history store', () => {
  beforeEach(() => {
    clearDownloadHistoryState()
    API.getHistory.mockReset()
    API.reconcileHistory.mockReset()
  })

  it('moves retried failures out of the failed list immediately', () => {
    upsertHistoryItem({
      id: 42,
      status: 'error',
      error: 'boom',
      filename: 'Broken.mp3',
      song: { name: 'Broken' },
    })

    const { failedHistory, sortedHistory } = useDownloadHistory()
    expect(failedHistory.value).toHaveLength(1)

    markHistoryRetrying(42)

    expect(failedHistory.value).toHaveLength(0)
    expect(sortedHistory.value).toHaveLength(0)
  })

  it('loads history without waiting on reconcile', async () => {
    API.getHistory.mockResolvedValue({
      data: [{ id: 7, status: 'done', title: 'Saved', song: { name: 'Saved' } }],
    })
    API.reconcileHistory.mockRejectedValue(new Error('timeout'))

    const ok = await refreshDownloadHistory({ reconcile: true })
    const { sortedHistory } = useDownloadHistory()

    expect(ok).toBe(true)
    expect(API.getHistory).toHaveBeenCalled()
    expect(sortedHistory.value).toHaveLength(1)
  })
})
