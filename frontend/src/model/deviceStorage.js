import { ref } from 'vue'
import { registerPlugin } from '@capacitor/core'

import { isCapacitorNative, usesEmbeddedServer } from './serverConnection'

const FolderPicker = registerPlugin('FolderPicker')
const EmbeddedServer = registerPlugin('EmbeddedServer')

const PATH_KEY = 'downtify-device-music-path'
const NAME_KEY = 'downtify-device-music-name'

export const deviceMusicPath = ref(read(PATH_KEY))
export const deviceMusicName = ref(read(NAME_KEY))
export const allFilesAccessGranted = ref(false)

let embeddedDefaultDir = ''

function read(key) {
  try {
    return localStorage.getItem(key) || ''
  } catch {
    return ''
  }
}

function persist(path, name) {
  deviceMusicPath.value = path || ''
  deviceMusicName.value = name || ''
  try {
    if (path) localStorage.setItem(PATH_KEY, path)
    else localStorage.removeItem(PATH_KEY)
    if (name) localStorage.setItem(NAME_KEY, name)
    else localStorage.removeItem(NAME_KEY)
  } catch {
    // ignore storage errors
  }
}

export function supportsDeviceStorage() {
  return isCapacitorNative() && usesEmbeddedServer()
}

export async function refreshAllFilesAccess() {
  if (!isCapacitorNative()) {
    allFilesAccessGranted.value = false
    return false
  }
  try {
    const res = await FolderPicker.hasAllFilesAccess()
    allFilesAccessGranted.value = Boolean(res?.granted)
  } catch {
    allFilesAccessGranted.value = false
  }
  return allFilesAccessGranted.value
}

export async function requestAllFilesAccess() {
  if (!isCapacitorNative()) return false
  try {
    const res = await FolderPicker.requestAllFilesAccess()
    allFilesAccessGranted.value = Boolean(res?.granted)
  } catch {
    await refreshAllFilesAccess()
  }
  return allFilesAccessGranted.value
}

export async function getDefaultMusicDir() {
  if (!isCapacitorNative()) return ''
  try {
    const res = await FolderPicker.getDefaultMusicDir()
    return res?.path || ''
  } catch {
    return ''
  }
}

async function embeddedDownloadDir() {
  if (embeddedDefaultDir) return embeddedDefaultDir
  if (!isCapacitorNative()) return ''
  try {
    const info = await EmbeddedServer.getInfo()
    embeddedDefaultDir = info?.downloadDir || ''
  } catch {
    embeddedDefaultDir = ''
  }
  return embeddedDefaultDir
}

/**
 * Opens the system folder picker and returns the chosen absolute filesystem
 * path so the embedded backend can be pointed at it. Throws ``AbortError`` when
 * the user cancels and ``Error('no-path')`` when the folder is not a plain
 * filesystem location (e.g. a cloud provider).
 */
export async function pickDeviceMusicFolder() {
  await requestAllFilesAccess()
  let result
  try {
    result = await FolderPicker.pickFolder()
  } catch (err) {
    if (err?.message === 'cancelled') {
      const abort = new Error('cancelled')
      abort.name = 'AbortError'
      throw abort
    }
    throw err
  }
  const path = String(result?.path || '').trim()
  if (!path) {
    throw new Error('no-path')
  }
  persist(path, result?.name || '')
  return path
}

/** Resets the chosen folder back to the shared music-library default. */
export async function useDefaultMusicFolder() {
  await requestAllFilesAccess()
  const path = await getDefaultMusicDir()
  persist('', '')
  return path
}

/**
 * Absolute folder the embedded backend currently downloads into: the
 * user-chosen path when set, otherwise the embedded server's own default.
 */
export async function activeDownloadRoot(serverMediaLocation = '') {
  const chosen = String(
    serverMediaLocation || deviceMusicPath.value || ''
  ).trim()
  if (chosen) return chosen
  return embeddedDownloadDir()
}

/** Index a freshly written file so it appears in the device's music library. */
export async function scanDownloadedFile(absolutePath) {
  if (!isCapacitorNative() || !absolutePath) return
  try {
    await FolderPicker.scanMedia({ path: absolutePath })
  } catch {
    // Best-effort; the file is already on disk regardless.
  }
}
