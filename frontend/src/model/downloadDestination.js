import { ref, computed } from 'vue'

const DESTINATION_KEY = 'downtify-download-destination'
const FOLDER_NAME_KEY = 'downtify-local-folder-name'
const HANDLE_DB = 'downtify-fs'
const HANDLE_STORE = 'directory'

const destination = ref(readDestination())
const localFolderName = ref(readFolderName())
const localFolderReady = ref(false)

let dirHandle = null

function readDestination() {
  const value = localStorage.getItem(DESTINATION_KEY)
  return value === 'local' ? 'local' : 'server'
}

function readFolderName() {
  return localStorage.getItem(FOLDER_NAME_KEY) || ''
}

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

async function pickLocalFolder() {
  const support = getLocalFolderSupport()
  if (!support.supported) {
    throw new Error(support.reason || 'unsupported')
  }
  const handle = await window.showDirectoryPicker({ mode: 'readwrite' })
  dirHandle = handle
  localFolderName.value = handle.name
  localFolderReady.value = true
  try {
    localStorage.setItem(FOLDER_NAME_KEY, handle.name)
  } catch {
    // ignore
  }
  await persistHandle(handle)
  return true
}

async function activateLocalDestination() {
  const support = getLocalFolderSupport()
  if (!support.supported) {
    throw new Error(support.reason || 'unsupported')
  }
  await pickLocalFolder()
  setDestination('local')
  return true
}

async function clearLocalFolder() {
  dirHandle = null
  localFolderName.value = ''
  localFolderReady.value = false
  try {
    localStorage.removeItem(FOLDER_NAME_KEY)
  } catch {
    // ignore
  }
  await clearStoredHandle()
  setDestination('server')
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
  const dir = segments.length
    ? await ensureDirHandle(handle, segments)
    : handle
  const fileHandle = await dir.getFileHandle(fileName, { create: true })
  const writable = await fileHandle.createWritable()
  await writable.write(blob)
  await writable.close()
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

  await writeBlobToFolder(filename, blob)
}

async function bootstrapLocalDestination() {
  if (destination.value !== 'local') return
  if (!supportsLocalFolder() || !localFolderName.value) {
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
    supportsLocalFolder: computed(() => supportsLocalFolder()),
    localFolderBlockReason: computed(() => getLocalFolderSupport().reason),
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
