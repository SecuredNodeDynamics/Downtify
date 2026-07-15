import { beforeEach, describe, expect, it } from 'vitest'

import {
  clearDownloadHistoryState,
  markHistoryRetrying,
  upsertHistoryItem,
  useDownloadHistory,
} from '../model/downloadHistory.js'

describe('download history store', () => {
  beforeEach(() => {
    clearDownloadHistoryState()
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
})
