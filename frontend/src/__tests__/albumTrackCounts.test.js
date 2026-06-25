import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ref, nextTick } from 'vue'

const { fetchAlbumTrackCounts } = vi.hoisted(() => ({
  fetchAlbumTrackCounts: vi.fn(),
}))

vi.mock('../model/api.js', () => ({
  default: {
    fetchAlbumTrackCounts,
  },
}))

import { useAlbumTrackCounts } from '../model/albumTrackCounts.js'

async function flushCounts() {
  await nextTick()
  await Promise.resolve()
  await Promise.resolve()
}

describe('albumTrackCounts', () => {
  beforeEach(() => {
    fetchAlbumTrackCounts.mockReset()
  })

  it('fetches counts for albums missing track_count', async () => {
    fetchAlbumTrackCounts.mockResolvedValue({
      data: { counts: { MPREb_a: 12 } },
    })

    const items = ref([
      {
        media_type: 'album',
        browse_id: 'MPREb_a',
        name: 'Album',
      },
    ])
    const { trackCountFor } = useAlbumTrackCounts(items)

    await flushCounts()

    expect(fetchAlbumTrackCounts).toHaveBeenCalledWith(['MPREb_a'])
    expect(trackCountFor(items.value[0])).toBe(12)
  })

  it('resolves getter sources', async () => {
    fetchAlbumTrackCounts.mockResolvedValue({
      data: { counts: { MPREb_b: 9 } },
    })

    const items = ref([
      {
        media_type: 'album',
        browse_id: 'MPREb_b',
        name: 'Album',
      },
    ])
    const { trackCountFor } = useAlbumTrackCounts(() => items.value)

    await flushCounts()

    expect(fetchAlbumTrackCounts).toHaveBeenCalledWith(['MPREb_b'])
    expect(trackCountFor(items.value[0])).toBe(9)
  })

  it('skips albums that already include track_count', async () => {
    const items = ref([
      {
        media_type: 'album',
        browse_id: 'MPREb_a',
        track_count: 8,
        name: 'Album',
      },
    ])
    const { trackCountFor } = useAlbumTrackCounts(items)

    await flushCounts()

    expect(fetchAlbumTrackCounts).not.toHaveBeenCalled()
    expect(trackCountFor(items.value[0])).toBe(8)
  })
})
