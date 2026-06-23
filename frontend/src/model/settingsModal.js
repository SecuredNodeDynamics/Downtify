import router from '../router'

export function openSettings(tab) {
  if (tab) {
    window.dispatchEvent(
      new CustomEvent('downtify:open-settings', { detail: { tab } })
    )
  }
  router.push({
    name: 'Settings',
    query: tab ? { tab } : {},
  })
}

export function openSettingsModal(tab) {
  openSettings(tab)
}

export function closeSettingsModal() {
  if (window.history.length > 1) {
    router.back()
    return
  }
  router.push({ name: 'Home' })
}

export function isSettingsModalOpen() {
  return router.currentRoute.value.name === 'Settings'
}
