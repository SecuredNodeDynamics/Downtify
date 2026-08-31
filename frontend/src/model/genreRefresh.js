import { ref } from 'vue'

import API from './api.js'

export const genreWarmupStatus = ref({
  status: 'idle',
  phase: '',
  current: 0,
  total: 0,
  error: '',
})

let pollTimer = null
let inFlight = null
let lastAutoStartUnknowns = -1

export function resetGenreLookupMemory() {
  lastAutoStartUnknowns = -1
  inFlight = null
  stopGenreWarmupPolling()
}

export function isGenreWarmupRunning(status = genreWarmupStatus.value) {
  return status?.status === 'running'
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
    if (res?.data?.status !== 'running') {
      stopGenreWarmupPolling()
    }
  } catch {
    stopGenreWarmupPolling()
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
