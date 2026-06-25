import { ref, unref, watch } from 'vue'

import API from './api'

export function mediaItemKey(item) {
  return String(item?.song_id || item?.browse_id || item?.url || '')
}

export function useLibraryOwnership(itemsSource) {
  const ownedKeys = ref(new Set())
  let requestId = 0

  async function refresh(items) {
    const list = (items || []).filter((item) => mediaItemKey(item))
    if (!list.length) {
      ownedKeys.value = new Set()
      return
    }

    const id = ++requestId
    try {
      const res = await API.checkLibraryOwned(list)
      if (id !== requestId) return
      const map = res.data?.owned || {}
      ownedKeys.value = new Set(
        Object.entries(map)
          .filter(([, owned]) => owned)
          .map(([key]) => key)
      )
    } catch {
      if (id !== requestId) return
      ownedKeys.value = new Set()
    }
  }

  watch(
    () => unref(itemsSource),
    (items) => {
      void refresh(items)
    },
    { immediate: true, deep: true }
  )

  function isOwned(item) {
    if (!item) return false
    return ownedKeys.value.has(mediaItemKey(item))
  }

  return { ownedKeys, isOwned, refresh }
}

export async function isMediaOwned(item) {
  const key = mediaItemKey(item)
  if (!key) return false
  try {
    const res = await API.checkLibraryOwned([item])
    return Boolean(res.data?.owned?.[key])
  } catch {
    return false
  }
}
