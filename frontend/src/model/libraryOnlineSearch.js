import { ref, watch, onUnmounted } from 'vue'

import API from './api'
import {
  matchesLibraryArtistName,
  normalizeLibrarySearchQuery,
} from './library'

export function onlineArtistsLabel(item) {
  if (Array.isArray(item?.artists) && item.artists.length) {
    return item.artists.join(', ')
  }
  return String(item?.artist || '').trim()
}

export function filterOnlineResultsForLibraryView(items, viewMode, query) {
  const q = normalizeLibrarySearchQuery(query)
  if (!q) return []
  const list = Array.isArray(items) ? items : []

  if (viewMode === 'albums') {
    return list.filter((item) => item?.media_type === 'album')
  }

  if (viewMode === 'tracks') {
    return list.filter((item) => item?.media_type !== 'album')
  }

  if (viewMode === 'genres') {
    return list.filter((item) => {
      if (item?.media_type === 'album') return true
      return Boolean(item?.name)
    })
  }

  return list.filter((item) => {
    const artist = onlineArtistsLabel(item)
    if (item?.media_type === 'album') {
      return matchesLibraryArtistName(artist, q)
    }
    return matchesLibraryArtistName(artist, q)
  })
}

export function useLibraryOnlineSearch(queryRef, viewModeRef, enabledRef) {
  const results = ref([])
  const loading = ref(false)
  const error = ref('')

  let timer = null
  let requestId = 0

  async function runSearch() {
    if (!enabledRef.value) {
      results.value = []
      loading.value = false
      error.value = ''
      return
    }

    const query = String(queryRef.value || '').trim()
    if (!query) {
      results.value = []
      loading.value = false
      error.value = ''
      return
    }

    const id = ++requestId
    loading.value = true
    error.value = ''

    try {
      const res = await API.search(query)
      if (id !== requestId) return
      if (res.status === 200) {
        results.value = filterOnlineResultsForLibraryView(
          res.data,
          viewModeRef.value,
          query
        )
      } else {
        results.value = []
        error.value = 'failed'
      }
    } catch {
      if (id !== requestId) return
      results.value = []
      error.value = 'failed'
    } finally {
      if (id === requestId) loading.value = false
    }
  }

  function scheduleSearch() {
    clearTimeout(timer)
    timer = setTimeout(runSearch, 350)
  }

  watch([queryRef, viewModeRef, enabledRef], scheduleSearch, { immediate: true })

  onUnmounted(() => {
    clearTimeout(timer)
    requestId += 1
  })

  return { results, loading, error }
}
