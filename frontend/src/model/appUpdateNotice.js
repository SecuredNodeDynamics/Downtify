import { isCapacitorNative } from './serverConnection'
import { appUpdateAvailable, checkDowntifyVersion } from './appVersion'
import { openSettingsModal } from './settingsModal'

let checkPromise = null
let bootstrapped = false
let periodicTimer = null
let foregroundListenersStarted = false
let lastRefreshAttemptAt = 0

// On native the launch check can fail because connectivity isn't ready yet
// right after a cold start (and the embedded-server reload). Retry with a
// backoff until the first successful check instead of giving up after one try,
// which previously left the header badge hidden until a manual Settings check.
const NATIVE_RETRY_DELAYS_MS = [2000, 5000, 15000, 30000, 60000]
// Re-check periodically so an update published while the app stays open is
// surfaced without requiring a relaunch.
const WEB_PERIODIC_INTERVAL_MS = 15 * 60 * 1000
const NATIVE_PERIODIC_INTERVAL_MS = 60 * 60 * 1000
const WEB_FOREGROUND_REFRESH_MIN_MS = 5 * 60 * 1000
const NATIVE_FOREGROUND_REFRESH_MIN_MS = 15 * 60 * 1000

export { appUpdateAvailable }

function delay(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

export async function refreshAppUpdateNotice(refreshCache = false) {
  lastRefreshAttemptAt = Date.now()
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
    if (document.visibilityState === 'hidden') return
    await delay(wait)
    if (await attemptUpdateCheck(true)) return
  }
}

function periodicIntervalMs() {
  return isCapacitorNative()
    ? NATIVE_PERIODIC_INTERVAL_MS
    : WEB_PERIODIC_INTERVAL_MS
}

function foregroundRefreshMinMs() {
  return isCapacitorNative()
    ? NATIVE_FOREGROUND_REFRESH_MIN_MS
    : WEB_FOREGROUND_REFRESH_MIN_MS
}

function startPeriodicUpdateChecks() {
  if (periodicTimer) return
  periodicTimer = window.setInterval(() => {
    if (document.visibilityState === 'hidden') return
    void refreshAppUpdateNotice(true)
  }, periodicIntervalMs())
}

function refreshWhenForegrounded() {
  if (document.visibilityState === 'hidden') return
  if (Date.now() - lastRefreshAttemptAt < foregroundRefreshMinMs()) return
  void refreshAppUpdateNotice(true)
}

function startForegroundUpdateChecks() {
  if (foregroundListenersStarted) return
  foregroundListenersStarted = true

  window.addEventListener('focus', refreshWhenForegrounded)
  window.addEventListener('online', refreshWhenForegrounded)
  document.addEventListener('visibilitychange', refreshWhenForegrounded)

  if (!isCapacitorNative()) return

  import('@capacitor/app')
    .then(({ App }) => {
      App.addListener('appStateChange', ({ isActive }) => {
        if (isActive) refreshWhenForegrounded()
      })
    })
    .catch(() => {
      // Native app lifecycle notifications are best-effort; the browser
      // focus/visibility listeners still keep the web app refreshed.
    })
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
  startForegroundUpdateChecks()
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
