import { isCapacitorNative } from './serverConnection'
import { appUpdateAvailable, checkDowntifyVersion } from './appVersion'
import { openSettingsModal } from './settingsModal'

let checkPromise = null
let bootstrapped = false
let periodicTimer = null

// On native the launch check can fail because connectivity isn't ready yet
// right after a cold start (and the embedded-server reload). Retry with a
// backoff until the first successful check instead of giving up after one try,
// which previously left the header badge hidden until a manual Settings check.
const NATIVE_RETRY_DELAYS_MS = [2000, 5000, 15000, 30000, 60000]
// Re-check periodically so an update published while the app stays open is
// surfaced without requiring a relaunch.
const PERIODIC_INTERVAL_MS = 6 * 60 * 60 * 1000

export { appUpdateAvailable }

function delay(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

export async function refreshAppUpdateNotice(refreshCache = false) {
  if (!refreshCache && checkPromise) {
    await checkPromise
    return appUpdateAvailable.value
  }

  checkPromise = checkDowntifyVersion({ refresh: refreshCache })
    .then(() => appUpdateAvailable.value)
    // Keep the last known availability on a transient failure (e.g. GitHub
    // timeout) rather than forcing the badge off and hiding a real update.
    .catch(() => appUpdateAvailable.value)
    .finally(() => {
      checkPromise = null
    })

  return checkPromise
}

async function attemptUpdateCheck(refreshCache) {
  try {
    await checkDowntifyVersion({ refresh: refreshCache })
    return true
  } catch {
    return false
  }
}

async function bootstrapNativeUpdateCheck() {
  for (const wait of NATIVE_RETRY_DELAYS_MS) {
    await delay(wait)
    if (await attemptUpdateCheck(true)) return
  }
}

function startPeriodicUpdateChecks() {
  if (periodicTimer) return
  periodicTimer = window.setInterval(() => {
    void refreshAppUpdateNotice(true)
  }, PERIODIC_INTERVAL_MS)
}

export function bootstrapAppUpdateNotice() {
  if (bootstrapped) return
  bootstrapped = true

  if (isCapacitorNative()) {
    void bootstrapNativeUpdateCheck()
  } else {
    void refreshAppUpdateNotice(true)
  }

  startPeriodicUpdateChecks()
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
