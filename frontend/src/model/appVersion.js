import { App } from '@capacitor/app'
import axios from 'axios'
import { ref } from 'vue'

import {
  buildApkUpdateStatus,
  isNewerApkVersion,
  pickApkAsset,
} from './apkUpdate.js'
import {
  buildApiBaseUrl,
  getServerConfig,
  isCapacitorNative,
} from './serverConnection.js'

const WEB_VERSION_KEY = 'version'
const SERVER_VERSION_KEY = 'downtify-server-version'

let cachedNativeVersion = ''
let nativeVersionPromise = null
let cachedStatus = null
let cachedAt = 0
const CACHE_TTL_MS = 60 * 60 * 1000

export const appUpdateAvailable = ref(false)

function publishUpdateAvailability(status) {
  appUpdateAvailable.value = Boolean(status?.update_available)
}

export function getBundledAppVersion() {
  return String(
    typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : '0.0.0'
  ).trim()
}

export function isValidSemver(value) {
  return typeof value === 'string' && /^\d+\.\d+\.\d+$/.test(value.trim())
}

export async function resolveNativeInstalledVersion() {
  if (!isCapacitorNative()) return ''

  if (cachedNativeVersion) return cachedNativeVersion

  if (!nativeVersionPromise) {
    nativeVersionPromise = App.getInfo()
      .then((info) => {
        const version = String(info?.version || '').trim()
        cachedNativeVersion = isValidSemver(version)
          ? version
          : getBundledAppVersion()
        return cachedNativeVersion
      })
      .catch(() => {
        cachedNativeVersion = getBundledAppVersion()
        return cachedNativeVersion
      })
      .finally(() => {
        nativeVersionPromise = null
      })
  }

  return nativeVersionPromise
}

export function getInstalledClientVersionSync() {
  if (!isCapacitorNative()) return ''
  return cachedNativeVersion || getBundledAppVersion()
}

export function readCachedServerVersion() {
  try {
    const stored = localStorage.getItem(SERVER_VERSION_KEY)
    return isValidSemver(stored) ? stored.trim() : ''
  } catch {
    return ''
  }
}

export function writeCachedServerVersion(version) {
  const trimmed = String(version || '').trim()
  if (!isValidSemver(trimmed)) return false
  try {
    localStorage.setItem(SERVER_VERSION_KEY, trimmed)
    return true
  } catch {
    return false
  }
}

export function readCachedWebVersion() {
  try {
    const stored = localStorage.getItem(WEB_VERSION_KEY)
    return isValidSemver(stored) ? stored.trim() : ''
  } catch {
    return ''
  }
}

export function sanitizeStoredVersions() {
  try {
    const legacy = localStorage.getItem(WEB_VERSION_KEY)
    if (legacy && !isValidSemver(legacy)) {
      localStorage.removeItem(WEB_VERSION_KEY)
    }
    const server = localStorage.getItem(SERVER_VERSION_KEY)
    if (server && !isValidSemver(server)) {
      localStorage.removeItem(SERVER_VERSION_KEY)
    }
  } catch {
    // ignore quota / private mode errors
  }
}

async function fetchLatestGithubRelease() {
  // A bare fetch on a freshly launched APK can hang indefinitely when the
  // radio is still negotiating connectivity. Bound it so the launch update
  // check fails fast and the retry loop can try again, instead of leaving the
  // header badge stuck until the user opens Settings.
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 15000)
  let response
  try {
    response = await fetch(
      'https://api.github.com/repos/SecuredNodeDynamics/Downtify/releases/latest',
      {
        headers: {
          Accept: 'application/vnd.github+json',
          'User-Agent': `Downtify/${getBundledAppVersion()}`,
        },
        signal: controller.signal,
      }
    )
  } finally {
    clearTimeout(timeout)
  }

  if (response.status === 404) return null
  if (!response.ok) {
    throw new Error(`GitHub release lookup failed with HTTP ${response.status}`)
  }

  return response.json()
}

async function fetchConnectedServerVersion() {
  try {
    const response = await axios.get(
      `${buildApiBaseUrl(getServerConfig())}/api/version`,
      {
        params: { t: Date.now() },
        timeout: 15000,
        headers: {
          Accept: 'application/json',
          'Cache-Control': 'no-cache',
        },
      }
    )
    const version = String(response.data || '').trim()
    if (!isValidSemver(version)) return readCachedServerVersion()
    writeCachedServerVersion(version)
    return version
  } catch {
    return readCachedServerVersion()
  }
}

export async function refreshConnectedServerVersion() {
  return fetchConnectedServerVersion()
}

function buildNativeUpdateStatus(installedVersion, serverVersion, release) {
  const githubStatus = release
    ? buildApkUpdateStatus(release, installedVersion)
    : {
        current_version: installedVersion,
        latest_version: null,
        update_available: false,
        release_url: 'https://github.com/SecuredNodeDynamics/Downtify/releases',
        apk_download_url: '',
        apk_name: '',
        source: 'github_apk',
        name: '',
        published_at: null,
        error: 'No GitHub release found.',
      }

  const versionMismatch = Boolean(
    serverVersion && serverVersion !== installedVersion
  )
  const needsApkUpdate = Boolean(githubStatus.update_available)
  const needsServerUpdate = Boolean(
    serverVersion && isNewerApkVersion(installedVersion, serverVersion)
  )
  const serverAhead = Boolean(
    serverVersion && isNewerApkVersion(serverVersion, installedVersion)
  )

  return {
    ...githubStatus,
    current_version: installedVersion,
    connected_server_version: serverVersion || '',
    version_mismatch: versionMismatch,
    needs_apk_update: needsApkUpdate || serverAhead,
    needs_server_update: needsServerUpdate,
    update_available: needsApkUpdate || needsServerUpdate || serverAhead,
    source: 'downtify',
  }
}

function buildWebUpdateStatus(data) {
  const current = String(data?.current_version || '').trim()
  const latest = String(data?.latest_version || '').trim()

  return {
    current_version: current,
    latest_version: latest || null,
    update_available: Boolean(data?.update_available),
    release_url: data?.release_url || '',
    apk_download_url: '',
    apk_name: '',
    connected_server_version: current,
    version_mismatch: false,
    needs_apk_update: false,
    needs_server_update: Boolean(
      latest && current && isNewerApkVersion(latest, current)
    ),
    source: data?.source || 'server',
    name: data?.name || '',
    published_at: data?.published_at || null,
    error: data?.error || '',
  }
}

export function getCachedUpdateStatus() {
  if (!cachedStatus) return null
  if (Date.now() - cachedAt >= CACHE_TTL_MS) return null

  if (isCapacitorNative()) {
    return {
      ...cachedStatus,
      current_version:
        getInstalledClientVersionSync() || cachedStatus.current_version,
    }
  }

  return { ...cachedStatus }
}

export async function checkDowntifyVersion({ refresh = false } = {}) {
  const now = Date.now()

  if (!refresh && cachedStatus && now - cachedAt < CACHE_TTL_MS) {
    if (isCapacitorNative()) {
      const installed =
        (await resolveNativeInstalledVersion()) ||
        getInstalledClientVersionSync()
      const status = {
        ...cachedStatus,
        current_version: installed,
        update_available: Boolean(
          cachedStatus.latest_version &&
            isNewerApkVersion(cachedStatus.latest_version, installed)
        ),
        needs_apk_update: Boolean(
          cachedStatus.latest_version &&
            isNewerApkVersion(cachedStatus.latest_version, installed)
        ),
      }
      publishUpdateAvailability(status)
      return status
    }
    const status = { ...cachedStatus }
    publishUpdateAvailability(status)
    return status
  }

  if (!isCapacitorNative()) {
    const response = await axios.get(
      `${buildApiBaseUrl(getServerConfig())}/api/check_update`,
      { params: { refresh }, timeout: 15000 }
    )
    const status = buildWebUpdateStatus(response.data || {})
    cachedStatus = status
    cachedAt = now
    publishUpdateAvailability(status)
    return status
  }

  const installed =
    (await resolveNativeInstalledVersion()) || getInstalledClientVersionSync()
  const [release, serverVersion] = await Promise.all([
    fetchLatestGithubRelease(),
    fetchConnectedServerVersion(),
  ])
  const status = buildNativeUpdateStatus(installed, serverVersion, release)
  cachedStatus = status
  cachedAt = now
  publishUpdateAvailability(status)
  return status
}

export function resetDowntifyVersionCache() {
  cachedStatus = null
  cachedAt = 0
  appUpdateAvailable.value = false
}

export { pickApkAsset }
