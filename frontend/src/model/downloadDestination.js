import { ref, computed } from 'vue'
import { registerPlugin } from '@capacitor/core'

import { isCapacitorNative } from './serverConnection'

const DESTINATION_KEY = 'downtify-download-destination'
const FOLDER_NAME_KEY = 'downtify-local-folder-name'
const LOCAL_MODE_KEY = 'downtify-local-save-mode'
const NATIVE_URI_KEY = 'downtify-native-tree-uri'
const HANDLE_DB = 'downtify-fs'
const HANDLE_STORE = 'directory'

const FolderPicker = registerPlugin('FolderPicker')

const destination = ref(readDestination())
const localFolderName = ref(readFolderName())
const localFolderReady = ref(false)
const localSaveMode = ref(readLocalSaveMode())

let dirHandle = null
let nativeTreeUri = readNativeTreeUri()

function readNativeTreeUri() {
  try {
    return localStorage.getItem(NATIVE_URI_KEY) || ''
  } catch {
    return ''
  }
}

function guessMimeType(name) {
  const ext = String(name || '').split('.').pop().toLowerCase()
  switch (ext) {
    case 'mp3':
      return 'audio/mpeg'
    case 'm4a':
    case 'mp4':
      return 'audio/mp4'
    case 'aac':
      return 'audio/aac'
    case 'opus':
      return 'audio/opus'
    case 'ogg':
      return 'audio/ogg'
    case 'flac':
      return 'audio/flac'
    case 'wav':
      return 'audio/wav'
    case 'lrc':
    case 'txt':
      return 'text/plain'
    case 'jpg':
    case 'jpeg':
      return 'image/jpeg'
    case 'png':
      return 'image/png'
    default:
      return 'application/octet-stream'
  }
}

function readDestination() {
  const value = localStorage.getItem(DESTINATION_KEY)
  return value === 'local' ? 'local' : 'server'
}

function readFolderName() {
  return localStorage.getItem(FOLDER_NAME_KEY) || ''
}

function readLocalSaveMode() {
  const value = localStorage.getItem(LOCAL_MODE_KEY)
  if (value === 'browser-downloads' || value === 'native') return value
  return isCapacitorNative() ? 'native' : 'folder'
}

const NATIVE_SUBDIR = 'Downtify'

function getLocalFolderSupport() {
  if (typeof window === 'undefined') {
    return { supported: false, reason: 'unavailable' }
  }
  if (!window.isSecureContext) {
    return { supported: false, reason: 'insecure' }
  }
  if (typeof window.showDirectoryPicker !== 'function') {
    return { supported: false, reason: 'browser' }
  }
  return { supported: true, reason: null }
}

function supportsBrowserDownloads() {
  return typeof window !== 'undefined' && typeof document !== 'undefined'
}

function getLocalSaveSupport() {
  if (isCapacitorNative()) {
    return { supported: true, mode: 'native', reason: null }
  }
  const folderSupport = getLocalFolderSupport()
  if (folderSupport.supported) {
    return { supported: true, mode: 'folder', reason: null }
  }
  if (supportsBrowserDownloads()) {
    return { supported: true, mode: 'browser-downloads', reason: null }
  }
  return { supported: false, mode: null, reason: folderSupport.reason }
}

function supportsLocalFolder() {
  return getLocalFolderSupport().supported
}

function openHandleDb() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(HANDLE_DB, 1)
    request.onupgradeneeded = () => {
      request.result.createObjectStore(HANDLE_STORE)
    }
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

async function readHandleFromDb() {
  const db = await openHandleDb()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(HANDLE_STORE, 'readonly')
    const req = tx.objectStore(HANDLE_STORE).get('downloads')
    req.onsuccess = () => resolve(req.result || null)
    req.onerror = () => reject(req.error)
  })
}

async function resolveDirHandle({ requestIfNeeded = false } = {}) {
  if (!supportsLocalFolder()) return null

  const candidates = []
  if (dirHandle) candidates.push(dirHandle)
  try {
    const stored = await readHandleFromDb()
    if (stored && stored !== dirHandle) candidates.push(stored)
  } catch (err) {
    console.warn('Could not read local download folder:', err)
  }

  for (const handle of candidates) {
    try {
      let permission = await handle.queryPermission({ mode: 'readwrite' })
      if (permission !== 'granted' && requestIfNeeded) {
        permission = await handle.requestPermission({ mode: 'readwrite' })
      }
      if (permission === 'granted') {
        dirHandle = handle
        localFolderReady.value = true
        return handle
      }
    } catch (err) {
      console.warn('Could not access local download folder:', err)
    }
  }

  localFolderReady.value = false
  return null
}

async function persistHandle(handle) {
  const db = await openHandleDb()
  await new Promise((resolve, reject) => {
    const tx = db.transaction(HANDLE_STORE, 'readwrite')
    tx.objectStore(HANDLE_STORE).put(handle, 'downloads')
    tx.oncomplete = () => resolve()
    tx.onerror = () => reject(tx.error)
  })
}

async function clearStoredHandle() {
  try {
    const db = await openHandleDb()
    await new Promise((resolve, reject) => {
      const tx = db.transaction(HANDLE_STORE, 'readwrite')
      tx.objectStore(HANDLE_STORE).delete('downloads')
      tx.oncomplete = () => resolve()
      tx.onerror = () => reject(tx.error)
    })
  } catch {
    // ignore
  }
}

function setDestination(value) {
  destination.value = value === 'local' ? 'local' : 'server'
  try {
    localStorage.setItem(DESTINATION_KEY, destination.value)
  } catch {
    // ignore
  }
  if (destination.value === 'server') {
    localFolderReady.value = false
  }
}

function setLocalMode(mode) {
  if (mode === 'browser-downloads' || mode === 'native') {
    localSaveMode.value = mode
  } else {
    localSaveMode.value = 'folder'
  }
  try {
    localStorage.setItem(LOCAL_MODE_KEY, localSaveMode.value)
  } catch {
    // ignore
  }
}

async function pickNativeFolder() {
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
  nativeTreeUri = result?.uri || ''
  if (!nativeTreeUri) {
    throw new Error('no-folder')
  }
  localFolderName.value = result?.name || 'Selected folder'
  localFolderReady.value = true
  setLocalMode('native')
  try {
    localStorage.setItem(NATIVE_URI_KEY, nativeTreeUri)
    localStorage.setItem(FOLDER_NAME_KEY, localFolderName.value)
  } catch {
    // ignore
  }
  return true
}

async function pickLocalFolder() {
  if (isCapacitorNative()) {
    return pickNativeFolder()
  }
  const support = getLocalFolderSupport()
  if (!support.supported) {
    throw new Error(support.reason || 'unsupported')
  }
  const handle = await window.showDirectoryPicker({ mode: 'readwrite' })
  dirHandle = handle
  localFolderName.value = handle.name
  localFolderReady.value = true
  setLocalMode('folder')
  try {
    localStorage.setItem(FOLDER_NAME_KEY, handle.name)
  } catch {
    // ignore
  }
  await persistHandle(handle)
  return true
}

async function activateLocalDestination() {
  const support = getLocalSaveSupport()
  if (!support.supported) {
    throw new Error(support.reason || 'unsupported')
  }
  if (support.mode === 'folder') {
    await pickLocalFolder()
  } else if (support.mode === 'native') {
    dirHandle = null
    await pickNativeFolder()
  } else {
    dirHandle = null
    localFolderName.value = 'Selected browser download location'
    localFolderReady.value = true
    setLocalMode('browser-downloads')
    try {
      localStorage.setItem(FOLDER_NAME_KEY, localFolderName.value)
    } catch {
      // ignore
    }
  }
  setDestination('local')
  return true
}

async function clearLocalFolder() {
  dirHandle = null
  nativeTreeUri = ''
  localFolderName.value = ''
  localFolderReady.value = false
  try {
    localStorage.removeItem(FOLDER_NAME_KEY)
    localStorage.removeItem(LOCAL_MODE_KEY)
    localStorage.removeItem(NATIVE_URI_KEY)
  } catch {
    // ignore
  }
  await clearStoredHandle()
  setDestination('server')
}

function downloadBlobWithBrowser(blob, filename) {
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  const segments = String(filename || 'download')
    .split('/')
    .filter(Boolean)
  link.href = url
  link.download = segments.pop() || 'download'
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

async function ensureDirHandle(root, parts) {
  let current = root
  for (const part of parts) {
    current = await current.getDirectoryHandle(part, { create: true })
  }
  return current
}

async function writeBlobToFolder(relativePath, blob) {
  const handle = await resolveDirHandle({ requestIfNeeded: true })
  if (!handle) {
    throw new Error('no-folder')
  }

  const segments = String(relativePath || '')
    .split('/')
    .filter(Boolean)
  if (!segments.length) return false

  const fileName = segments.pop()
  const dir = segments.length ? await ensureDirHandle(handle, segments) : handle
  const fileHandle = await dir.getFileHandle(fileName, { create: true })
  const writable = await fileHandle.createWritable()
  await writable.write(blob)
  await writable.close()
  return true
}

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onloadend = () => {
      const result = String(reader.result || '')
      const comma = result.indexOf(',')
      resolve(comma >= 0 ? result.slice(comma + 1) : result)
    }
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(blob)
  })
}

async function writeBlobToDevice(relativePath, blob) {
  const segments = String(relativePath || '')
    .split('/')
    .filter(Boolean)
  if (!segments.length) throw new Error('no-filename')

  const data = await blobToBase64(blob)

  if (nativeTreeUri) {
    await FolderPicker.writeFile({
      uri: nativeTreeUri,
      path: segments.join('/'),
      data,
      mimeType: guessMimeType(segments[segments.length - 1]),
    })
    return true
  }

  const { Filesystem, Directory } = await import('@capacitor/filesystem')
  const path = `${NATIVE_SUBDIR}/${segments.join('/')}`
  const dirPath = path.slice(0, path.lastIndexOf('/'))

  if (dirPath) {
    try {
      await Filesystem.mkdir({
        path: dirPath,
        directory: Directory.Documents,
        recursive: true,
      })
    } catch {
      // Directory already exists; ignore.
    }
  }

  await Filesystem.writeFile({
    path,
    data,
    directory: Directory.Documents,
    recursive: true,
  })
  return true
}

async function saveToLocalMachine(downloadUrl, filename) {
  if (destination.value !== 'local' || !downloadUrl) return

  const response = await fetch(downloadUrl)
  if (!response.ok) {
    throw new Error(`Download failed (${response.status})`)
  }
  const blob = await response.blob()

  if (!filename) {
    throw new Error('no-filename')
  }

  if (localSaveMode.value === 'native' && isCapacitorNative()) {
    await writeBlobToDevice(filename, blob)
    return
  }

  if (localSaveMode.value === 'folder' && supportsLocalFolder()) {
    await writeBlobToFolder(filename, blob)
    return
  }

  downloadBlobWithBrowser(blob, filename)
}

async function bootstrapLocalDestination() {
  if (destination.value !== 'local') return

  if (isCapacitorNative()) {
    setLocalMode('native')
    if (nativeTreeUri) {
      try {
        const res = await FolderPicker.checkPermission({ uri: nativeTreeUri })
        if (res?.granted) {
          localFolderReady.value = true
          if (!localFolderName.value) {
            localFolderName.value = 'Selected folder'
          }
          return
        }
      } catch {
        // Fall through to clearing the stale URI.
      }
      nativeTreeUri = ''
      try {
        localStorage.removeItem(NATIVE_URI_KEY)
      } catch {
        // ignore
      }
    }
    localFolderReady.value = false
    localFolderName.value = ''
    return
  }

  if (localSaveMode.value === 'browser-downloads') {
    if (!supportsBrowserDownloads()) {
      await clearLocalFolder()
      return
    }
    localFolderReady.value = true
    if (!localFolderName.value) {
      localFolderName.value = 'Selected browser download location'
    }
    return
  }

  if (!supportsLocalFolder() || !localFolderName.value) {
    const support = getLocalSaveSupport()
    if (support.supported && support.mode === 'browser-downloads') {
      localFolderName.value = 'Selected browser download location'
      localFolderReady.value = true
      setLocalMode('browser-downloads')
      return
    }
    await clearLocalFolder()
    return
  }

  await resolveDirHandle()
}

bootstrapLocalDestination()

export function useDownloadDestination() {
  return {
    destination,
    localFolderName,
    localFolderReady,
    localSaveMode,
    supportsLocalFolder: computed(() => supportsLocalFolder()),
    localFolderBlockReason: computed(() => {
      const support = getLocalSaveSupport()
      return support.supported ? null : support.reason
    }),
    usesBrowserDownloads: computed(
      () => localSaveMode.value === 'browser-downloads'
    ),
    usesNativeDownloads: computed(() => localSaveMode.value === 'native'),
    isLocal: computed(() => destination.value === 'local'),
    hasLocalFolder: computed(
      () => destination.value === 'local' && Boolean(localFolderName.value)
    ),
    setDestination,
    pickLocalFolder,
    activateLocalDestination,
    clearLocalFolder,
    saveToLocalMachine,
  }
}
