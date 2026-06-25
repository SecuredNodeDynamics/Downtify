import { isCapacitorNative } from './serverConnection'
import { appUpdateAvailable, checkDowntifyVersion } from './appVersion'
import { openSettingsModal } from './settingsModal'

let checkPromise = null
let bootstrapped = false

export { appUpdateAvailable }

export async function refreshAppUpdateNotice(refreshCache = false) {
  if (!refreshCache && checkPromise) {
    await checkPromise
    return appUpdateAvailable.value
  }

  checkPromise = checkDowntifyVersion({ refresh: refreshCache })
    .then(() => appUpdateAvailable.value)
    .catch(() => {
      appUpdateAvailable.value = false
      return false
    })
    .finally(() => {
      checkPromise = null
    })

  return checkPromise
}

export function bootstrapAppUpdateNotice() {
  if (bootstrapped) return
  bootstrapped = true

  const run = () => {
    void refreshAppUpdateNotice(true)
  }

  if (isCapacitorNative()) {
    window.setTimeout(run, 2000)
    return
  }

  run()
}

export function useAppUpdateNotice() {
  function openUpdateSettings() {
    openSettingsModal('help')
  }

  return {
    updateAvailable: appUpdateAvailable,
    refresh: refreshAppUpdateNotice,
    openUpdateSettings,
  }
}
