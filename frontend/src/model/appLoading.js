import { ref } from 'vue'

const visible = ref(false)

let showTimer = null
let hideTimer = null
let pendingLoads = 0
let shownAt = 0

const SHOW_DELAY_MS = 520
const MIN_VISIBLE_MS = 220

export function useAppLoading() {
  return { visible }
}

export function beginAppLoading() {
  pendingLoads += 1
  if (showTimer || visible.value) return

  showTimer = setTimeout(() => {
    showTimer = null
    if (pendingLoads <= 0) return
    shownAt = Date.now()
    visible.value = true
  }, SHOW_DELAY_MS)
}

export function endAppLoading() {
  pendingLoads = Math.max(0, pendingLoads - 1)
  if (pendingLoads > 0) return

  if (showTimer) {
    clearTimeout(showTimer)
    showTimer = null
  }

  if (!visible.value) return

  const elapsed = Date.now() - shownAt
  const remaining = Math.max(0, MIN_VISIBLE_MS - elapsed)

  if (hideTimer) clearTimeout(hideTimer)
  hideTimer = setTimeout(() => {
    hideTimer = null
    if (pendingLoads === 0) visible.value = false
  }, remaining)
}

export function resetAppLoading() {
  pendingLoads = 0
  visible.value = false
  shownAt = 0
  if (showTimer) clearTimeout(showTimer)
  if (hideTimer) clearTimeout(hideTimer)
  showTimer = null
  hideTimer = null
}
