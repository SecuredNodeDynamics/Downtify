import { Capacitor, registerPlugin } from '@capacitor/core'

const GITHUB_REPO = 'SecuredNodeDynamics/Downtify'
const GITHUB_RELEASES_URL = `https://github.com/${GITHUB_REPO}/releases`
const GITHUB_API_BASE = `https://api.github.com/repos/${GITHUB_REPO}`
const APK_NAME_RE = /^downtify-(\d+\.\d+\.\d+)(?:-debug)?\.apk$/i
const CACHE_TTL_MS = 60 * 60 * 1000

const ApkInstaller = registerPlugin('ApkInstaller')

let cachedStatus = null
let cachedAt = 0

export function parseApkVersion(value) {
  const match = String(value || '').match(/(\d+)\.(\d+)\.(\d+)/)
  if (!match) return null
  return [Number(match[1]), Number(match[2]), Number(match[3])]
}

export function isNewerApkVersion(latest, current) {
  const next = parseApkVersion(latest)
  const installed = parseApkVersion(current)
  if (!next || !installed) return false
  for (let index = 0; index < 3; index += 1) {
    if (next[index] > installed[index]) return true
    if (next[index] < installed[index]) return false
  }
  return false
}

export function pickApkAsset(assets = []) {
  const matches = (assets || [])
    .map((asset) => {
      const name = String(asset?.name || '')
      const match = name.match(APK_NAME_RE)
      if (!match) return null
      return {
        name,
        version: match[1],
        download_url: asset.browser_download_url || '',
        size: asset.size || 0,
        isLegacyDebugName: /-debug\.apk$/i.test(name),
      }
    })
    .filter(Boolean)

  if (!matches.length) return null

  matches.sort((left, right) => {
    const leftParts = parseApkVersion(left.version) || [0, 0, 0]
    const rightParts = parseApkVersion(right.version) || [0, 0, 0]
    for (let index = 0; index < 3; index += 1) {
      if (leftParts[index] !== rightParts[index]) {
        return rightParts[index] - leftParts[index]
      }
    }
    if (left.isLegacyDebugName !== right.isLegacyDebugName) {
      return left.isLegacyDebugName ? 1 : -1
    }
    return 0
  })

  return matches[0]
}

export function buildApkUpdateStatus(release, currentVersion) {
  const apk = pickApkAsset(release?.assets)
  const latestVersion = apk?.version || ''
  const updateAvailable = Boolean(
    latestVersion && isNewerApkVersion(latestVersion, currentVersion)
  )

  return {
    current_version: currentVersion,
    latest_version: latestVersion || null,
    update_available: updateAvailable,
    release_url: release?.html_url || GITHUB_RELEASES_URL,
    apk_download_url: apk?.download_url || '',
    apk_name: apk?.name || '',
    source: 'github_apk',
    name: release?.name || release?.tag_name || '',
    published_at: release?.published_at || null,
    error: apk ? '' : 'No APK asset found on the latest GitHub release.',
  }
}

async function fetchLatestRelease() {
  const response = await fetch(`${GITHUB_API_BASE}/releases/latest`, {
    headers: {
      Accept: 'application/vnd.github+json',
      'User-Agent': `Downtify-Android/${__APP_VERSION__ || '0.0.0'}`,
    },
  })

  if (response.status === 404) {
    return null
  }

  if (!response.ok) {
    throw new Error(`GitHub release lookup failed with HTTP ${response.status}`)
  }

  return response.json()
}

export function getInstalledApkVersion() {
  return String(__APP_VERSION__ || '0.0.0').trim()
}

export async function checkApkUpdate({ refresh = false } = {}) {
  const currentVersion = getInstalledApkVersion()
  const now = Date.now()

  if (!refresh && cachedStatus && now - cachedAt < CACHE_TTL_MS) {
    return {
      ...cachedStatus,
      current_version: currentVersion,
      update_available: Boolean(
        cachedStatus.latest_version &&
          isNewerApkVersion(cachedStatus.latest_version, currentVersion)
      ),
    }
  }

  const release = await fetchLatestRelease()
  if (!release) {
    const empty = {
      current_version: currentVersion,
      latest_version: null,
      update_available: false,
      release_url: GITHUB_RELEASES_URL,
      apk_download_url: '',
      apk_name: '',
      source: 'github_apk',
      name: '',
      published_at: null,
      error: 'No GitHub release found.',
    }
    cachedStatus = empty
    cachedAt = now
    return empty
  }

  const status = buildApkUpdateStatus(release, currentVersion)
  cachedStatus = status
  cachedAt = now
  return status
}

export async function installApkUpdate(downloadUrl) {
  const url = String(downloadUrl || '').trim()
  if (!url) {
    throw new Error('Missing APK download URL')
  }
  if (!Capacitor.isNativePlatform()) {
    throw new Error('APK updates are only available in the Android app')
  }
  await ApkInstaller.downloadAndInstall({ url })
}

export function resetApkUpdateCache() {
  cachedStatus = null
  cachedAt = 0
}
