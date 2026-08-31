import { ref } from 'vue'

import API from './api.js'
import { notifyLibraryChanged } from './librarySession.js'

export const genreWarmupStatus = ref({
  status: 'idle',
  phase: '',
  current: 0,
  total: 0,
  error: '',
  started_at: '',
  updated_at: '',
  tagged_tracks: 0,
  total_tracks: 0,
})

const STALL_MS = 45_000

let pollTimer = null
let inFlight = null
let lastAutoStartUnknowns = -1
let lastPolledStatus = ''

export function resetGenreLookupMemory() {
  lastAutoStartUnknowns = -1
  inFlight = null
  lastPolledStatus = ''
  stopGenreWarmupPolling()
}

export function isGenreWarmupRunning(status = genreWarmupStatus.value) {
  return status?.status === 'running'
}

export function genreWarmupPercent(status = genreWarmupStatus.value) {
  const total = Number(status?.total) || 0
  const current = Number(status?.current) || 0
  if (total <= 0) return 0
  return Math.max(0, Math.min(100, Math.round((current / total) * 100)))
}

export function isGenreWarmupStalled(
  status = genreWarmupStatus.value,
  now = Date.now()
) {
  if (status?.status !== 'running') return false
  const phase = String(status?.phase || '')
  if (phase === 'library' || !phase) return false
  const raw = status.updated_at || ''
  const then = Date.parse(raw)
  if (!Number.isFinite(then)) return false
  return now - then > STALL_MS
}

export function stopGenreWarmupPolling() {
  if (!pollTimer) return
  clearInterval(pollTimer)
  pollTimer = null
}

async function refreshGenreWarmupStatus() {
  try {
    const res = await API.getLibraryGenresStatus()
    if (res?.data) genreWarmupStatus.value = res.data
    const status = res?.data?.status || ''
    if (status !== 'running') {
      if (lastPolledStatus === 'running' && status) {
        notifyLibraryChanged()
      }
      lastPolledStatus = status
      stopGenreWarmupPolling()
      return
    }
    lastPolledStatus = status
  } catch {
    // Keep polling through brief network errors so the bar does not
    // freeze on "running" after a single failed status check.
  }
}

export function startGenreWarmupPolling() {
  if (pollTimer) return
  pollTimer = setInterval(() => {
    void refreshGenreWarmupStatus()
  }, 2000)
  void refreshGenreWarmupStatus()
}

export async function startLibraryGenreLookup() {
  const res = await API.startLibraryGenreRefresh()
  if (res?.data) genreWarmupStatus.value = res.data
  lastPolledStatus = res?.data?.status || 'running'
  startGenreWarmupPolling()
  return res?.data
}

export async function cancelLibraryGenreLookup() {
  const res = await API.cancelLibraryGenreRefresh()
  if (res?.data) genreWarmupStatus.value = res.data
  lastPolledStatus = res?.data?.status || 'cancelled'
  startGenreWarmupPolling()
  return res?.data
}

export async function ensureLibraryGenreLookup(unknownCount) {
  if (!unknownCount) {
    lastAutoStartUnknowns = 0
    if (!isGenreWarmupRunning()) stopGenreWarmupPolling()
    return
  }
  if (inFlight) return inFlight
  inFlight = (async () => {
    try {
      const res = await API.getLibraryGenresStatus()
      const current = res?.data || {}
      genreWarmupStatus.value = current
      if (current.status === 'running') {
        startGenreWarmupPolling()
        return
      }
      if (current.status === 'cancelled') return
      if (
        current.status === 'complete' &&
        unknownCount === lastAutoStartUnknowns
      ) {
        return
      }
      lastAutoStartUnknowns = unknownCount
      await startLibraryGenreLookup()
    } catch {
      // Library refresh can still pick up genres from the server cache.
    }
  })().finally(() => {
    inFlight = null
  })
  return inFlight
}
