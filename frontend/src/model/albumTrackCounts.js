import { ref, unref, watch } from 'vue'

import API from './api'

function resolveSource(source) {
  const raw = unref(source)
  if (typeof raw === 'function') return raw()
  return raw
}

export function useAlbumTrackCounts(itemsSource) {
  const countsByBrowseId = ref({})
  let requestId = 0

  async function refresh(items) {
    const browseIds = [
      ...new Set(
        (items || [])
          .filter(
            (item) =>
              item?.media_type === 'album' &&
              item.browse_id &&
              !Number(item.track_count) &&
              countsByBrowseId.value[item.browse_id] == null
          )
          .map((item) => item.browse_id)
      ),
    ]
    if (!browseIds.length) return

    const id = ++requestId
    try {
      const res = await API.fetchAlbumTrackCounts(browseIds)
      if (id !== requestId) return
      const counts = res.data?.counts || {}
      if (!Object.keys(counts).length) return
      countsByBrowseId.value = { ...countsByBrowseId.value, ...counts }
    } catch {
      if (id !== requestId) return
    }
  }

  watch(
    () => resolveSource(itemsSource),
    (items) => {
      void refresh(items)
    },
    { immediate: true, deep: true }
  )

  function trackCountFor(item) {
    if (!item) return null
    const fromItem = Number(item.track_count)
    if (Number.isFinite(fromItem) && fromItem > 0) return fromItem
    const fromLookup = Number(countsByBrowseId.value[item.browse_id])
    if (Number.isFinite(fromLookup) && fromLookup > 0) return fromLookup
    return null
  }

  return { countsByBrowseId, trackCountFor }
}
