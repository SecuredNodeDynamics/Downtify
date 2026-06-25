import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ref, nextTick } from 'vue'

const { checkLibraryOwned } = vi.hoisted(() => ({
  checkLibraryOwned: vi.fn(),
}))

vi.mock('../model/api.js', () => ({
  default: {
    checkLibraryOwned,
  },
}))

import {
  mediaItemKey,
  useLibraryOwnership,
  isMediaOwned,
} from '../model/libraryOwnership.js'

async function flushOwnership() {
  await nextTick()
  await Promise.resolve()
  await Promise.resolve()
}

describe('libraryOwnership', () => {
  beforeEach(() => {
    checkLibraryOwned.mockReset()
  })

  it('builds stable keys from song or browse ids', () => {
    expect(mediaItemKey({ song_id: 'track:1', browse_id: 'album:1' })).toBe(
      'track:1'
    )
    expect(mediaItemKey({ browse_id: 'album:1' })).toBe('album:1')
  })

  it('marks owned items from the API response', async () => {
    checkLibraryOwned.mockResolvedValue({
      data: { owned: { 'track:1': true, 'album:2': false } },
    })

    const items = ref([
      { song_id: 'track:1', name: 'Owned Song' },
      { browse_id: 'album:2', media_type: 'album', name: 'Missing Album' },
    ])
    const { isOwned } = useLibraryOwnership(items)

    await flushOwnership()

    expect(isOwned(items.value[0])).toBe(true)
    expect(isOwned(items.value[1])).toBe(false)
  })

  it('checks a single item with isMediaOwned', async () => {
    checkLibraryOwned.mockResolvedValue({
      data: { owned: { 'track:9': true } },
    })

    const owned = await isMediaOwned({ song_id: 'track:9', name: 'Song' })
    expect(owned).toBe(true)
  })
})
