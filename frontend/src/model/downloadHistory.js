import { ref, computed } from 'vue'

import API from './api'

const history = ref([])
export const historyRevision = ref(0)

let historyRefreshTimer = 0
let historyFetchSeq = 0

const TERMINAL_STATUSES = new Set(['done', 'skipped', 'error'])

function historyDate(item) {
  return item?.completed_at || item?.updated_at || item?.created_at || ''
}

export function sortHistoryItems(items) {
  return [...(items || [])].sort((a, b) => {
    const cmp = historyDate(b).localeCompare(historyDate(a))
    if (cmp !== 0) return cmp
    return (b.id || 0) - (a.id || 0)
  })
}

function historyIdentity(item) {
  if (item?.id != null) return `id:${item.id}`
  const songId = String(item?.song_id || item?.song?.song_id || '')
  if (songId) return `song:${songId}`
  return ''
}

export function upsertHistoryItem(item) {
  if (!item || typeof item !== 'object') return

  const normalized = {
    ...item,
    status: String(item.status || '').trim() || 'done',
  }
  const identity = historyIdentity(normalized)
  if (!identity) return

  const existingIndex = history.value.findIndex(
    (entry) => historyIdentity(entry) === identity
  )
  if (existingIndex === -1) {
    history.value = sortHistoryItems([normalized, ...history.value])
    return
  }

  const next = [...history.value]
  next[existingIndex] = { ...next[existingIndex], ...normalized }
  history.value = sortHistoryItems(next)
}

export async function refreshDownloadHistory({ reconcile = true } = {}) {
  const seq = ++historyFetchSeq
  try {
    if (reconcile) {
      await API.reconcileHistory()
    }
    const res = await API.getHistory(500, false)
    if (seq !== historyFetchSeq) return false
    history.value = sortHistoryItems(Array.isArray(res.data) ? res.data : [])
    return true
  } catch {
    return false
  }
}

function scheduleRefreshDownloadHistory() {
  if (historyRefreshTimer) {
    clearTimeout(historyRefreshTimer)
  }
  historyRefreshTimer = setTimeout(() => {
    historyRefreshTimer = 0
    void refreshDownloadHistory()
  }, 250)
}

export function notifyDownloadHistory({ immediate = false } = {}) {
  historyRevision.value += 1
  if (immediate) {
    if (historyRefreshTimer) {
      clearTimeout(historyRefreshTimer)
      historyRefreshTimer = 0
    }
    void refreshDownloadHistory()
    return
  }
  scheduleRefreshDownloadHistory()
}

export function clearDownloadHistoryState() {
  history.value = []
}

export function useDownloadHistory() {
  const sortedHistory = computed(() =>
    sortHistoryItems(
      history.value.filter((item) => TERMINAL_STATUSES.has(item.status))
    )
  )

  return {
    history,
    sortedHistory,
    historyRevision,
    refreshDownloadHistory,
    notifyDownloadHistory,
    upsertHistoryItem,
    clearDownloadHistoryState,
    sortHistoryItems,
    historyDate,
  }
}
